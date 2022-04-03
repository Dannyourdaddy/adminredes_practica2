
import rrdtool
import os
from pysnmp.hlapi import *
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
w, h = A4


def consultaSNMP(comunidad:str,host:str, oid:str, version:int):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        # hace la solicitud getsnmp
        getCmd(SnmpEngine(),
               CommunityData(comunidad, mpModel=version),
               UdpTransportTarget((host, 161)),  # udp
               ContextData(),
               ObjectType(ObjectIdentity(oid))))

    if errorIndication:
        pass
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            varB = (' = '.join([x.prettyPrint() for x in varBind]))
            resultado = varB.split()[2]  # se agarra la ultima parte de la consulta
        return resultado

def Bases(c):
    RDD(c + "/multicast.rrd")
    RDD(c + "/ipv4.rrd")
    RDD(c + "/icmp.rrd")
    RDD(c + "/octets.rrd")
    RDD(c + "/ports.rrd")

def RDD(nombreRRD: str):
    ret = rrdtool.create(nombreRRD,
                            "--start",
                            'N',
                            "--step",
                            '30',
                            "DS:octets:COUNTER:30:U:U",  # DS: Octetos de entrada :
                            "RRA:AVERAGE:0.5:1:32")   # RRA: Cada 60 segs de hace un AVERAGE:

    if ret:
        print(rrdtool.error())


def GenerarGraficas(c):
    nuevaGrafica(c +"/multicast.png", c + '/multicast.rrd')
    nuevaGrafica(c +"/ipv4.png", c + '/ipv4.rrd')
    nuevaGrafica(c +"/icmp.png", c + '/icmp.rrd')
    nuevaGrafica(c +"/octets.png", c + '/octets.rrd')
    nuevaGrafica(c +"/ports.png", c + '/ports.rrd')


def nuevaGrafica(nombre_grafica:str, base_RRD:str):
    tiempo_actual = int(time.time())
    tiempo_inicial = tiempo_actual - 690
    ret = rrdtool.graph(nombre_grafica,
                    "--start",str(tiempo_inicial),
                    "--end","N",
                    "--vertical-label=Bytes/s",
                    "--title=grafica " + nombre_grafica,
                    "DEF:trafico=" + base_RRD +":octets:AVERAGE",
                    "CDEF:escalaIn=trafico,8,*",
                    "LINE3:escalaIn#0000FF:Trafico de entrada")

def updateListaConsultas(comunidad:str, host:str, version:int) -> list:
    lista_con = [0,0,0,0,0]


    lista_con[0]= consultaSNMP(comunidad, host ,"1.3.6.1.2.1.2.2.1.18.1", version)
    rrdtool.update(comunidad + '_' + host + '/multicast.rrd', "N:" + lista_con[0])
    rrdtool.dump(comunidad + '_' + host + '/multicast.rrd',  comunidad + '_' + host + '/multicast.xml')

    lista_con[1]= consultaSNMP(comunidad, host ,"1.3.6.1.2.1.4.10.0", version)
    rrdtool.update(comunidad + '_' + host + '/ipv4.rrd', "N:" + lista_con[1])
    rrdtool.dump(comunidad + '_' + host + '/ipv4.rrd',  comunidad + '_' + host + '/ipv4.xml')

    lista_con[2] = consultaSNMP(comunidad, host, "1.3.6.1.2.1.5.8.0", version)
    rrdtool.update(comunidad + '_' + host + '/icmp.rrd', "N:" + lista_con[2])
    rrdtool.dump(comunidad + '_' + host + '/icmp.rrd', comunidad + '_' + host + '/icmp.xml')

    lista_con[3] = consultaSNMP(comunidad, host, "1.3.6.1.2.1.7.2.0", version)
    rrdtool.update(comunidad + '_' + host + '/octets.rrd', "N:" + lista_con[3])
    rrdtool.dump(comunidad + '_' + host + '/octets.rrd', comunidad + '_' + host + '/octets.xml')

    lista_con[4] = consultaSNMP(comunidad, host, "1.3.6.1.2.1.7.4.0", version)
    rrdtool.update(comunidad + '_' + host + '/ports.rrd', "N:" + lista_con[4])
    rrdtool.dump(comunidad + '_' + host + '/ports.rrd', comunidad + '_' + host + '/ports.xml')

    return lista_con





respuesta = int(input('Bienvenido al gestor de agentes\n'
                      'Puedes escoger la opción que desees\n'
                      '-----------------------------------------\n'
                      '  1.-Resumen de agentes\n'
                      '  2.-Agregar agente\n'
                      '  3.-Eliminar Agente\n'
                      '  4.-Generar Reportes de agentes\n'
                      '  5.-Ver trafico de contabilidad\n'
                      '  0.- Salir\n'))
while respuesta != 0:

    if respuesta == 1:
        print('------------Agentes registrados-------------')
        with open('text.txt') as archivo: #cuento el numero de lineas para el for que aplicare mas a bajo
            agentes = archivo.readlines()
            nulineas = len(agentes)
            if nulineas < 1:
                print('---------no hay agentes registrados---------')
                time.sleep(3)
                os.system("clear")
            else:
                os.system("clear")
                print('+-----------------+---------------+---------')
                print('|   Comunidad     |     host      | status |')
                print('+-----------------+---------------+---------')
                i = 0
                for agente in agentes:
                    i = i + 1
                    disp = agente.split()
                    consulta = consultaSNMP(disp[0],disp[2],'1.3.6.1.2.1.1.1.0', int(disp[1])-1)
                    cadena = "|" + str(i) + '.-' + "{:<14}|{:>15}|".format(disp[0], disp[2])
                    if consulta:
                        print(cadena + '   Up   |')
                    else:
                        print(cadena + '   Down |')


    #segunda opción del Menu
    elif respuesta == 2:
        r = 's'
        while r == 's':
            print('Para agregar un agente por favor inserte\n----------------')
            print('nombre de comunidad')
            comunidad = input()
            print('versión')
            version = input()
            print('Ip del agente')
            ip = input()
            com = consultaSNMP(comunidad, ip, "1.3.6.1.2.1.1.1.0", int(version)-1)
            if com:
                comando = comunidad +' '+ version +' ' + ip
                archivo = open("text.txt","a")
                archivo.write(comando+'\n')
                archivo.close
                try:
                    os.mkdir(comunidad + '_' + ip)
                except:
                    pass
                Bases(comunidad + '_' + ip)
                inicio = time.time()
                fin = inicio + 180
                while True:
                    print(updateListaConsultas(comunidad, ip, int(version)-1))
                    inicio = time.time()
                    if not inicio < fin:
                        break
                GenerarGraficas(comunidad + '_' + ip)

                print('Se agrego agente con exito')

            else:
                print('No se reconoce el agente, verifique su creación')
            print('Quieres agregar otro agente  s/n')
            r = input()
        os.system("clear")


    # tercera opción del menu
    elif respuesta == 3:
        print('Proceso de eliminación\n----------------')
        archivo = open("text.txt")
        with open('text.txt') as numerolineas:
            lineas = sum(1 for line in numerolineas)
        if lineas < 1:
            print('-------no hay agentes registrados-------')
            time.sleep(3)
            os.system("clear")
        else:
            for i in range(lineas):     #proceso a enlistar los agentes en donde pongo solo la primera palabra de cada linea
                agente = archivo.readline().split()
                print(str(i+1)+'.-'+agente[0])

            archivo.close()
            print('Qué agente quieres eliminar')
            resp = input() #este va a ser la linea donde se selecionará el agente a borrar
            archivo = open("text.txt","r") #se abre el archivo para lectura
            lineass = archivo.readlines()
            archivo.close()
            archivo = open("text.txt", "w")#se abre archivo para escritura
            pos=int(resp) #fijo la linea que se va a borrar
            linea=lineass[pos-1]  #le baje una posicion porque los conteos siempre empiezan en 0
            lineass.remove(linea)  #procedo a borrar la linea de mi txt


            for linea in lineass:
                archivo.write(linea)
            archivo.close()
            print('Agente eliminado')
            time.sleep(3)
            os.system("clear")


    # cuarta opción del menu
    elif respuesta == 4:
        print('Generando reporte')
        c = canvas.Canvas("reporte.pdf", pagesize=A4)
        text = c.beginText(200, h - 50)
        text.setFont("Times-Roman", 13)

        with open('text.txt') as archivo: #cuento el numero de lineas para el for que aplicare mas a bajo
            agentes = archivo.readlines()
            nulineas = len(agentes)
            if nulineas < 1:
                text.textLines("REPORTE DE AGENTES")
                x = 50
                y = h - 65
                c.line(x, y, x + 500, y)
                c.drawText(text)
                text = c.beginText(140, h - 150)
                text.textLine("-----NO HAY AGENTES REGISTRADOS-------")
                c.drawText(text)
            else:
                i = 0
                for agente in agentes:
                    i = i + 1
                    disp = agente.split()
                    consulta = consultaSNMP(disp[0],disp[2],'1.3.6.1.2.1.1.1.0', int(disp[1])-1)
                    if consulta:
                        text = c.beginText(200, h - 50)
                        text.textLines("REPORTE DE AGENTES")
                        x = 50
                        y = h - 65
                        c.line(x, y, x + 500, y)
                        c.drawText(text)
                        text = c.beginText(50, h - 80)
                        text.setFont("Helvetica", 12)
                        if consulta == "Linux":
                            text.textLine(str(i) + ".- Agente   = Sistema operativo " + str(consulta))
                            text.textLines("Comunidad = " + disp[0] + "\nHost            = " + disp[2] + "\nVersión       = " + disp[1])
                            com = consultaSNMP(disp[0],disp[2],'1.3.6.1.2.1.2.1.0', int(disp[1])-1)
                            text.textLine("Interfaces   = " + str(com))
                            com = consultaSNMP(disp[0], disp[2], '1.3.6.1.2.1.1.3.0', int(disp[1]) - 1)
                            text.textLine("Tiempo_activo= " + str(com) + "seg")
                            c.drawImage("img/ubuntu.jpg", 400, h - 140, width=120, height=70)
                            c.drawImage(disp[0] + "_" + disp[2] + "/multicast.png", 25, h - 300, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/ipv4.png", 25, h - 460, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/octets.png", 300, h - 300, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/icmp.png", 300, h - 460, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/ports.png", 140, h - 620, width=270, height=130)
                        else:
                            text.textLine(str(i) + ".- Agente   = Sistema operativo Windows")
                            text.textLines("Comunidad = " + disp[0] + "\nHost            = " + disp[2] + "\nVersión       = " + disp[1])
                            com = consultaSNMP(disp[0], disp[2], '1.3.6.1.2.1.2.1.0', int(disp[1]) - 1)
                            text.textLine("Interfaces   = " + str(com))
                            com = consultaSNMP(disp[0], disp[2], '1.3.6.1.2.1.1.3.0', int(disp[1]) - 1)
                            text.textLine("Tiempo activo= " + str(com) + "seg")
                            c.drawImage("img/wind.jpg", 400, h - 140, width=120, height=70)
                            c.drawImage(disp[0] + "_" + disp[2] + "/multicast.png", 28, h - 300, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/ipv4.png", 28, h - 460, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/octets.png", 300, h - 300, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/icmp.png", 300, h - 460, width=270, height=130)
                            c.drawImage(disp[0] + "_" + disp[2] + "/ports.png", 200, h - 640, width=270, height=130)
                        c.drawText(text)
                        c.showPage()  # comando para pasar de pagina
                    else:
                        pass
        c.save()
        time.sleep(3)
        print("reporte generado de manera exitosa")
        time.sleep(1)
        os.system("clear")


    elif respuesta == 5:
        os.system("clear")
        print('Monitorizar un servicio\n----------------')
        archivo = open("text.txt")
        with open('text.txt') as numerolineas:
            lineas = sum(1 for line in numerolineas)
        if lineas < 1:
            print('-------no hay agentes registrados-------')
            time.sleep(3)
            os.system("clear")
        else:
            for i in range(lineas):  # proceso a enlistar los agentes en donde pongo solo la primera palabra de cada linea
                agente = archivo.readline().split()
                print(str(i + 1) + '.-' + agente[0])

            archivo.close()
            print('Que agente quieres monitorizar')
            resp1 = input()  # este va a ser la linea donde se selecionará el agente a monitorizar
            os.system('clear')
            print('Resumen de contabilidad agente:\n----------------------------------')

            print('Agente:'+agente[0]+'\nDirección del agente :'+ agente[2])
            monitorizar = consultaSNMP(agente[0], agente[2], '1.3.6.1.2.1.6.13.1.1.0.0.0.0.3000.0.0.0.0.0',
                                       int(agente[1]) - 1)
            print('TCP actual en particular conexión:'+ monitorizar)
            monitorizar = consultaSNMP(agente[0], agente[2], '1.3.6.1.2.1.6.13.1.2.0.0.0.0.3000.0.0.0.0.0',
                                       int(agente[1]) - 1)
            print('Dirección ip local para TCP:' + monitorizar)
            monitorizar = consultaSNMP(agente[0], agente[2], '1.3.6.1.2.1.6.13.1.3.0.0.0.0.3000.0.0.0.0.0',
                                       int(agente[1]) - 1)
            print('Numero de puerto local:'+monitorizar)
            monitorizar = consultaSNMP(agente[0], agente[2], '1.3.6.1.2.1.6.13.1.4.0.0.0.0.3000.0.0.0.0.0',
                                       int(agente[1]) - 1)
            print('Dirección IP remota:' + monitorizar)
            monitorizar = consultaSNMP(agente[0], agente[2], '1.3.6.1.2.1.6.13.1.5.0.0.0.0.3000.0.0.0.0.0',
                                       int(agente[1]) - 1)
            print('Numero de puerto remoto:' + monitorizar)
            monitorizar = consultaSNMP(agente[0], agente[2], '1.3.6.1.2.1.6.19.1.7.1.4.0.0.0.0.3000.1.4.0.0.0.0.0',
                                       int(agente[1]) - 1)
            print('Estado de conexión:' + monitorizar)

    else:
        print('no se entiende tu respuesta')
        time.sleep(2)
        os.system("clear")


    respuesta = int(input(
        '---------------------\n'
        'Bienvenido al gestor de agentes\n'
        'Puedes escoger la opción que desees\n'
        '--------------------------\n'
        '  1.-Resumen de agentes\n'
        '  2.-Agregar agente\n'
        '  3.-Eliminar Agente\n'
        '  4.-Generar Reportes de agentes\n'
        '  5.-Ver trafico de contabilidad\n'
        '  0.- Salir\n'))
