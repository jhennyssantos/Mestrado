#!/usr/bin/env python

import time
import os
import sys
import string
import MySQLdb
import math
from datetime import datetime, timedelta
from operator import itemgetter


def conectaBanco():
 
    HOST = "localhost"
    USER = "root"
    PASSWD = "mysql"
    BANCO = "dash_db5"
 
    try:
        conecta = MySQLdb.connect(HOST, USER, PASSWD)
        conecta.select_db(BANCO)
 
    except MySQLdb.Error, e:
        print "Erro: Banco nao encontrado",e
        menu = raw_input()
        os.system("clear")
        menu()
    
    return conecta

def definirTempoInicialBuffer(conecta, vetor):
    
    cursor = conecta.cursor()
    sql="SELECT * FROM  dash_bufferlevel WHERE fk_execution=%d"%int(vetor[0])
    try:
         cursor.execute(sql)
         buffers = cursor.fetchall()
              
         start_time = datetime.strptime(buffers[0][1], '%Y-%m-%dT%H:%M:%S.%fZ') 
              
         #fazer o start_time ser o maior e o finish_time ser o menor tempo
         maior_time_inicial = start_time
            
    except MySQLdb.Error, e:
          print "Erro: " + sql
          print e
            
    for i in range(1,len(vetor)):
        sql="SELECT * FROM  dash_bufferlevel WHERE fk_execution=%d"%int(vetor[i])
        try:
            cursor.execute(sql)
            buffers = cursor.fetchall()
              
            start_time = datetime.strptime(buffers[0][1], '%Y-%m-%dT%H:%M:%S.%fZ') 
              
            #fazer o start_time ser o maior e o finish_time ser o menor tempo se forem respectivamente, maior e menor
            #que maior_time_inicial e menor_time_final
            if start_time > maior_time_inicial:
                maior_time_inicial = start_time
            
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
            
    return maior_time_inicial
    
def definirTempoFinalBuffer(conecta, executions):
 
    cursor = conecta.cursor()
    sql="SELECT * FROM  dash_bufferlevel WHERE fk_execution=%d"%int(executions[0])
    try:
         buffers = 0
         cursor.execute(sql)
         buffers = cursor.fetchall()
              
         finish_time = datetime.strptime(buffers[len(buffers) - 1][1], '%Y-%m-%dT%H:%M:%S.%fZ') 
         #print"\n----------------------------\n"
         #print " ID: %s\n FinishTime: %s"%(int(executions[0]), finish_time)
              
         #fazer o start_time ser o maior e o finish_time ser o menor tempo
         menor_time_final = finish_time
    
    except MySQLdb.Error, e:
          print "Erro: " + sql
          print e
            
    
    for i in range(1,len(executions)):
        sql="SELECT * FROM  dash_bufferlevel WHERE fk_execution=%d"%int(executions[i])
        try:
            buffers = 0
            cursor.execute(sql)
            buffers = cursor.fetchall()
              
            finish_time = datetime.strptime(buffers[len(buffers) - 1][1], '%Y-%m-%dT%H:%M:%S.%fZ') 
            #print"\n----------------------------\n"
            #print " ID: %s\n FinishTime: %s"%(int(executions[i]), finish_time)
              
            #fazer o start_time ser o maior e o finish_time ser o menor tempo se forem respectivamente, maior e menor
            #que maior_time_inicial e menor_time_final
            if finish_time < menor_time_final:
                menor_time_final = finish_time
              
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
            
    return menor_time_final
#alinha as execucoes para que as sessoes sejam avaliadas no periodo em que todas 
#estivessem reproduzindo video, ao mesmo tempo
def definirTempoInicialSegmento(conecta, vetor):
    
    cursor = conecta.cursor()
    sql="SELECT time, start_time, finish_time FROM  dash_throughseg WHERE fk_execution=%d"%int(vetor[0])
    try:
         cursor.execute(sql)
         segmentos = cursor.fetchall()
              
         start_time = datetime.strptime(segmentos[0][1], '%Y-%m-%dT%H:%M:%S.%fZ') 
         #print"\n----------------------------\n"
         #print " ID: %s\n StartTime: %s"%(int(vetor[0]), start_time)
              
         #fazer o start_time ser o maior e o finish_time ser o menor tempo
         maior_time_inicial = start_time
    
    except MySQLdb.Error, e:
          print "Erro: " + sql
          print e
            
    for i in range(1,len(vetor)):
        sql="SELECT time, start_time, finish_time FROM dash_throughseg WHERE fk_execution=%d"%int(vetor[i])
        try:
            cursor.execute(sql)
            segmentos = cursor.fetchall()
              
            start_time = datetime.strptime(segmentos[0][1], '%Y-%m-%dT%H:%M:%S.%fZ') 
            #print"\n----------------------------\n"
            #print " ID: %s\n StartTime: %s"%(int(vetor[i]), start_time)
              
            #fazer o start_time ser o maior e o finish_time ser o menor tempo se forem respectivamente, maior e menor
            #que maior_time_inicial e menor_time_final
            if start_time > maior_time_inicial:
                maior_time_inicial = start_time
            
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
            
    return maior_time_inicial
    
def definirTempoFinalSegmento(conecta, executions):
 
    cursor = conecta.cursor()
    sql="SELECT time, start_time, finish_time FROM  dash_throughseg WHERE fk_execution=%d"%int(executions[0])
    try:
         cursor.execute(sql)
         segmentos = cursor.fetchall()
              
         finish_time = datetime.strptime(segmentos[len(segmentos) - 1][2], '%Y-%m-%dT%H:%M:%S.%fZ') 
         #print"\n----------------------------\n"
         #print " ID: %s\n FinishTime: %s"%(int(executions[0]), finish_time)
              
         #fazer o start_time ser o maior e o finish_time ser o menor tempo
         menor_time_final = finish_time
    
    except MySQLdb.Error, e:
          print "Erro: " + sql
          print e
            
    
    for i in range(1,len(executions)):
        sql="SELECT time, start_time, finish_time FROM dash_throughseg WHERE fk_execution=%d"%int(executions[i])
        try:
            cursor.execute(sql)
            segmentos = cursor.fetchall()
              
            finish_time = datetime.strptime(segmentos[len(segmentos) - 1][2], '%Y-%m-%dT%H:%M:%S.%fZ') 
            #print"\n----------------------------\n"
            #print " ID: %s\n FinishTime: %s"%(int(executions[i]), finish_time)
              
            #fazer o start_time ser o maior e o finish_time ser o menor tempo se forem respectivamente, maior e menor
            #que maior_time_inicial e menor_time_final
            if finish_time < menor_time_final:
                menor_time_final = finish_time
              
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
            
    return menor_time_final

#alinha as execucoes para que as sessoes sejam avaliadas no periodo em que todas 
#estivessem reproduzindo video, ao mesmo tempo
def definirTempoInicialExecution(conecta, vetor):
    
    cursor = conecta.cursor()
    sql="SELECT * FROM  dash_execution WHERE id=%d"%int(vetor[0])
    try:
         cursor.execute(sql)
         execution = cursor.fetchone()
         
         start_time = datetime.strptime(execution[1], '%Y-%m-%dT%H:%M:%S.%fZ') 
         #print"\n----------------------------\n"
         #print " ID: %s\n StartTime: %s"%(int(vetor[0]), start_time)
              
         #fazer o start_time ser o maior e o finish_time ser o menor tempo
         maior_time_inicial = start_time
    
    except MySQLdb.Error, e:
          print "Erro: " + sql
          print e
            
    for i in range(1,len(vetor)):
        sql="SELECT * FROM dash_execution WHERE id=%d"%int(vetor[i])
        try:
            cursor.execute(sql)
            execution = cursor.fetchone()
              
            start_time = datetime.strptime(execution[1], '%Y-%m-%dT%H:%M:%S.%fZ') 
            #print"\n----------------------------\n"
            #print " ID: %s\n StartTime: %s"%(int(vetor[i]), start_time)
              
            #fazer o start_time ser o maior e o finish_time ser o menor tempo se forem respectivamente, maior e menor
            #que maior_time_inicial e menor_time_final
            if start_time > maior_time_inicial:
                maior_time_inicial = start_time
            
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
            
    return maior_time_inicial
    
def definirTempoFinalExecution(conecta, executions):
 
    cursor = conecta.cursor()
    sql="SELECT * FROM  dash_execution WHERE id=%d"%int(executions[0])
    try:
         cursor.execute(sql)
         execution = cursor.fetchone()
              
         finish_time = datetime.strptime(execution[2], '%Y-%m-%dT%H:%M:%S.%fZ') 
         #print"\n----------------------------\n"
         #print " ID: %s\n FinishTime: %s"%(int(executions[0]), finish_time)
              
         #fazer o start_time ser o maior e o finish_time ser o menor tempo
         menor_time_final = finish_time
    
    except MySQLdb.Error, e:
          print "Erro: " + sql
          print e
            
    
    for i in range(1,len(executions)):
        sql="SELECT * FROM  dash_execution WHERE id=%d"%int(executions[0])
        try:
            cursor.execute(sql)
            execution = cursor.fetchone()
              
            finish_time = datetime.strptime(execution[2], '%Y-%m-%dT%H:%M:%S.%fZ') 
            #print"\n----------------------------\n"
            #print " ID: %s\n FinishTime: %s"%(int(executions[i]), finish_time)
              
            #fazer o start_time ser o maior e o finish_time ser o menor tempo se forem respectivamente, maior e menor
            #que maior_time_inicial e menor_time_final
            if finish_time < menor_time_final:
                menor_time_final = finish_time
              
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
            
    return menor_time_final


'''Funcao para coletar a qtde de trocas a media de amplitude por execucao e a media entre as execucoes informadas'''        
def coletarTrocasAmplitudes(conecta):
    executions = str(raw_input("\nDigite o(s) Id(s) da(s) execucao(oes) separados por espaco: "))
    executions = map(int, executions.split())
    #Corte para tempo de sessao total
    inicial_time = definirTempoInicialExecution(conecta, executions)
    final_time = definirTempoFinalExecution(conecta, executions)
    timeSession =  final_time - inicial_time
    timeSession = timeSession.total_seconds()
    print "Tempo da Sessao: %s"%timeSession
    
    cursor = conecta.cursor()
    sum_switch_up_count = 0
    sum_switch_down_count = 0
    average_amplitudes_pos = 0
    average_amplitudes_neg = 0
    
    for i in range(0,len(executions)):
        sql="SELECT time, start_time, finish_time, quality, bitrate FROM dash_throughseg WHERE fk_execution=%d"%int(executions[i])
        try:
            cursor.execute(sql)
            segmentos = cursor.fetchall()
              
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
        
        switch_up_count = 0
        switch_down_count = 0
        average_switch_amplitude_video = 0
        bitrates_list=[]
        amplitudes_pos = []
        amplitudes_neg = []
        amplitudes_pos_list = []
        amplitudes_neg_list = []
        bitrate_last = (int(segmentos[0][4]) + 100) #kbps
        
        #Contar qtde de trocas e a ampplitude das trocas
        for seg in segmentos:
            start_time_seg = datetime.strptime(seg[1], '%Y-%m-%dT%H:%M:%S.%fZ')
            finish_time_seg = datetime.strptime(seg[2], '%Y-%m-%dT%H:%M:%S.%fZ')
            if start_time_seg >= inicial_time and finish_time_seg <= final_time:
                bitrate = (int(seg[4]) + 100)
                bitrates_list.append(bitrate)
            
                if bitrate > bitrate_last: 
                    switch_up_count += 1
                    amplitudes_pos = [bitrate_last, bitrate, abs(bitrate_last - bitrate)]
                    amplitudes_pos_list.append(amplitudes_pos)
                    
                if bitrate < bitrate_last: 
                    switch_down_count += 1
                    amplitudes_neg = [bitrate_last, bitrate, abs(bitrate_last - bitrate)]
                    amplitudes_neg_list.append(amplitudes_neg)
                
                bitrate_last = bitrate
        
        #Media das amplitudes positivas entre as representacoes das trocas
        sum_amplitudes_pos_video = 0
        for amplitude in amplitudes_pos_list:
            sum_amplitudes_pos_video += amplitude[2]
        
         #Media das amplitudes negativas entre as representacoes das trocas
        sum_amplitudes_neg_video = 0
        for amplitude in amplitudes_neg_list:
            sum_amplitudes_neg_video += amplitude[2]
            
        if(len(amplitudes_pos_list) != 0):
           average_switch_amplitude_pos_video = sum_amplitudes_pos_video/len(amplitudes_pos_list)
        else:
            average_switch_amplitude_pos_video = 0
            
        if(len(amplitudes_neg_list) != 0):
           average_switch_amplitude_neg_video = sum_amplitudes_neg_video/len(amplitudes_neg_list)
        else:
            average_switch_amplitude_neg_video = 0
        
        sum_switch_up_count += switch_up_count 
        sum_switch_down_count += switch_down_count 
        
        average_amplitudes_pos += average_switch_amplitude_pos_video 
        average_amplitudes_neg += average_switch_amplitude_neg_video 
        
        print "ID: %d"%int(executions[i]) 
        print "Qtde de segmentos: %d"%len(segmentos) 
        print "Switchs Pos: %d"%switch_up_count 
        print "Switchs Neg: %d"%switch_down_count 
        print "SwitchAmplitudesAverage Pos: %f"%average_switch_amplitude_pos_video
        print "SwitchAmplitudesAverage Neg: %f"%average_switch_amplitude_neg_video
        
    print "==================================="
    print "SwitchsAverage Pos: %f"%(float(sum_switch_up_count)/len(executions))
    print "SwitchsAverage Neg: %f"%(float(sum_switch_down_count)/len(executions))
    print "AmplitudeAverage Pos: %f"%(float(average_amplitudes_pos)/len(executions))
    print "AmplitudeAverage Neg: %f"%(float(average_amplitudes_neg)/len(executions))

'''Funcao para coletar a taxa media por execucao, a media dessas medias e a justica entre as execucoes informadas'''        
def coletarTaxaJustica(conecta, executions):
    
    
    inicial_time = definirTempoInicialExecution(conecta, executions)
    final_time = definirTempoFinalExecution(conecta, executions)
    expectResult = str(raw_input("\nDigite o recurso esperado: "))
    
    deltaTime =  final_time - inicial_time
    deltaTime = deltaTime.total_seconds()
    
    cursor = conecta.cursor()
    
    gotResult = 0 # kbps bytes da sessao/tempo da sessao
    fairness=0
    xiSum = 0
    xiSum2 = 0
    xiCount = 0
    averageBitRateResultSum = 0

    for i in range(0,len(executions)):
        sql="SELECT time, start_time, finish_time, size_seg, duration, quality, bitrate FROM dash_throughseg WHERE fk_execution=%d"%int(executions[i])
        try:
            cursor.execute(sql)
            segmentos = cursor.fetchall()
              
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
        
        segCount=0
        bitratesSum=0
        bitsSum=0
        bitrateSum=0
        durationSum=0
        
        for seg in segmentos:
            start_time_seg = datetime.strptime(seg[1], '%Y-%m-%dT%H:%M:%S.%fZ')
            finish_time_seg = datetime.strptime(seg[2], '%Y-%m-%dT%H:%M:%S.%fZ')
            if start_time_seg >= inicial_time and finish_time_seg <= final_time:
                #bits = float(seg[3]) #bits 
                #bits = bits/1000.0 #kbits 
                #bitsSum  += bits
                duration_segment = float(seg[4]) #duracao do segmento em segundos 
                durationSum  += duration_segment 
                bitrate = float(seg[6]) + 100 #kbps  
                bitrateSum  += (bitrate) * duration_segment
                bitratesSum  += bitrate 
                segCount += 1

        averageBitRateResult = bitrateSum/deltaTime     
        #averageBitRateResult = bitrateSum/durationSum     
        gotResult = averageBitRateResult     
        
        averageBitRateResultSum += averageBitRateResult    
  
        xi = float(gotResult)/float(expectResult)
        xiSum += xi
        xi2 = xi * xi
        xiSum2 += xi2

        xiCount += 1
    
        print "ID: %d"%int(executions[i]) 
        print "Qtde de segmentos: %d"%len(segmentos) 
        print "Bitrate Average kbps: "+ str(averageBitRateResult)
        print "gotResult: "+ str(gotResult)
        print "Duracao da sessao: "+ str(deltaTime)
        print "Duracao da Total dos segmentos: "+ str(durationSum)
        #print "Xi da Sessao: "+ str(xi)
        #print "Xi2 da Sessao: "+ str(xi2)
        #print "GotResult em kbps da Sessao: "+ str(gotResult)

    print "==================================="
    fairness =  (xiSum*xiSum)/(xiCount * xiSum2)
    unfairness = math.sqrt(1-fairness)
    averageBitRateResultMedia = averageBitRateResultSum/xiCount
    print "xiCount: "+ str(xiCount)
    print "Justica: "+ str(fairness)
    print "Injustica: "+ str(unfairness)
    print "Media BitRate: "+ str(averageBitRateResultMedia)
    #print "xiSum: "+ str(xiSum)


'''Funcao para coletar a qtde de interrupcoes, a duracao media das interrupcoes por execucao e a media entre as execucoes informadas'''        
def coletarStallsDuracoes(conecta, executions):
   
    
    inicial_time = definirTempoInicialExecution(conecta, executions)
    final_time = definirTempoFinalExecution(conecta, executions)
    timeSession =  final_time - inicial_time
    timeSession = timeSession.total_seconds()
    print "Tempo da Sessao: %s"%timeSession

    BMin = 0.5
    cursor = conecta.cursor()
    
    sum_stall_count = 0
    average_stalls_durations = 0
    abr_sum = 0
    for i in range(0,len(executions)):
        sql="SELECT * FROM dash_bufferlevel WHERE fk_execution = %d" %int(executions[i])
        sql2="SELECT time, start_time, finish_time, size_seg, duration, quality, bitrate FROM dash_throughseg WHERE fk_execution=%d"%int(executions[i])
        sql3="SELECT * FROM dash_execution WHERE id = %d" %int(executions[i])

        try:
            cursor.execute(sql)
            buffers = cursor.fetchall()

            cursor.execute(sql2)
            segmentos = cursor.fetchall()
            
            cursor.execute(sql3)
            execution = cursor.fetchone()

        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
        
        
        inicial_time_ind = datetime.strptime(execution[1], '%Y-%m-%dT%H:%M:%S.%fZ')
        final_time_ind = datetime.strptime(execution[2], '%Y-%m-%dT%H:%M:%S.%fZ')
        timeSessionInd =  final_time_ind - inicial_time_ind
        timeSessionInd = timeSessionInd.total_seconds()
        print "Tempo da Sessao Individual: %s"%timeSessionInd
        
        inicial_time_seg = datetime.strptime(segmentos[0][1], '%Y-%m-%dT%H:%M:%S.%fZ')
        final_time_seg = datetime.strptime(segmentos[len(segmentos)-1][2], '%Y-%m-%dT%H:%M:%S.%fZ')
        timeSessionSeg =  final_time_seg - inicial_time_seg
        timeSessionSeg = timeSessionSeg.total_seconds()
        print "Tempo da Sessao Individual Segmento: %s"%timeSessionSeg
    
        sum_video_times = 0.0
        rebuffer_video_count = 0
        rebuffer_video_flag = True
        durations_video_list = []
        durations_video = []
        bufferlevel_video_last = int(buffers[0][2])
        
        #Contar qtde de interrupcoes e a duracao de cada interrupcao
        for buffer in buffers:
            time_buffer = datetime.strptime(buffer[1], '%Y-%m-%dT%H:%M:%S.%fZ')
            bufferlevelvideo = float(buffer[2])
            
            if time_buffer >= inicial_time and time_buffer <= final_time:
                               
                if bufferlevelvideo <= BMin and bufferlevelvideo < bufferlevel_video_last: 
                        if rebuffer_video_flag == True:
                            time1 = time_buffer
                            deltaTime1 =  time1 - inicial_time
                            deltaTime1 = deltaTime1.total_seconds()
                            rebuffer_video_flag = False
                elif bufferlevelvideo > BMin and bufferlevelvideo > bufferlevel_video_last:
                        if rebuffer_video_flag == False:
                            time2 = time_buffer
                            deltaTime2 =  time2 - inicial_time
                            deltaTime2 = deltaTime2.total_seconds()
                            rebuffer_video_flag = True
                        
                            deltaTime = time2 - time1
                            deltaTime = deltaTime.total_seconds()
                                            
                            rebuffer_video_count += 1
                            durations_video = [rebuffer_video_count, deltaTime]
                            durations_video_list.append(durations_video)
                            
                            sum_video_times += deltaTime
                            
                            #print "Paradas "+str(rebuffer_video_count) +" "+ str(deltaTime)
                            #print "Soma dos Tempos"+str(sum_video_times)
                            
                bufferlevel_video_last = bufferlevelvideo
            
        #Media das duracoes das rebufferizacoes de video      
        if(len(durations_video_list) != 0):
            average_duration_rebuffer_video = float(sum_video_times)/float(rebuffer_video_count)
        else:
            average_duration_rebuffer_video = 0       
        
        br_sum = 0 
        duration_sum = 0 
        for seg in segmentos:
            br = float(seg[6]) + 100
            br_sum += br * float(seg[4])
            duration_sum += float(seg[4])

        abr = br_sum/timeSession 
        #abr = br_sum/timeSession 
        #abr = br_sum/(timeSession - sum_video_times)

        abr_sum += abr
        
        print "ID: %d"%int(executions[i]) 
        print "Qtde de Interrupcoes: %d"%rebuffer_video_count
        print "Duracao Total das Interrupcoes: %f"%sum_video_times
        print "Duracao Media das Interrupcoes: %f"%average_duration_rebuffer_video
        print "Qtde de segmentos: %d"%len(segmentos) 
        print "Bitrate Average kbps: "+ str(abr)

        sum_stall_count += rebuffer_video_count
        average_stalls_durations += average_duration_rebuffer_video
        abrmedia = abr_sum/len(executions)
    print "==================================="
    print "Tempo de Sessao com corte: "+str(timeSession)
    print "Qtde Media de Interrupcoes: %f"%(float(sum_stall_count)/len(executions))
    print "Media de Duracao das Interrupcoes: %f"%(float(average_stalls_durations)/len(executions))    
    print "Media BitRate abr: "+ str(abrmedia)


'''Funcao para coletar a qtde de interrupcoes, a duracao media das interrupcoes por execucao e a media entre as execucoes informadas'''        
def coletarPopularity(conecta, executions):
   
    
    #Corte para tempo de sessao total
    inicial_time = definirTempoInicialExecution(conecta, executions)
    final_time = definirTempoFinalExecution(conecta, executions)
    timeSession =  final_time - inicial_time
    timeSession = timeSession.total_seconds()
    print "Tempo da Sessao: %s"%timeSession

    cursor1 = conecta.cursor()       
    cursor2 = conecta.cursor()       

    for i in range(0,len(executions)):
        
        sql1="SELECT * FROM dash_execution WHERE id=%d"%int(executions[i])
        sql2="SELECT time, start_time, finish_time, size_seg, duration, quality, bitrate FROM dash_throughseg WHERE fk_execution=%d"%int(executions[i])

        try:
            cursor1.execute(sql1)
            cursor2.execute(sql2)
            exect = cursor1.fetchone()
            segmentos = cursor2.fetchall()

            print exect
            
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
                
        bitrates_list=[]
        dict_bitrates={}
        for seg in segmentos:            
            start_time_seg = datetime.strptime(seg[1], '%Y-%m-%dT%H:%M:%S.%fZ')
            finish_time_seg = datetime.strptime(seg[2], '%Y-%m-%dT%H:%M:%S.%fZ')
            if start_time_seg >= inicial_time and finish_time_seg <= final_time:
                
                bitrate_parameter = float(seg[6]) + 100
                bitrates_list.append(bitrate_parameter)

       #Pegar a popularidade de cada taxa
        dict_bitrates = dict((i,float(bitrates_list.count(i))/float(len(bitrates_list))*100) for i in bitrates_list)
        dict_bitrates_sorted = sorted(dict_bitrates.items(), key=itemgetter(0))
        
        print executions[i] 
        print dict_bitrates_sorted 
                    

    print "==================================="
    
'''Funcao para coletar a instabilidade por execucao e a media entre as execucoes informadas'''        
def coletarInst(conecta, executions):
    
    
    #Corte para tempo de sessao total
    inicial_time = definirTempoInicialExecution(conecta, executions)
    final_time = definirTempoFinalExecution(conecta, executions)
    timeSession =  final_time - inicial_time
    timeSession = timeSession.total_seconds()
    print "Tempo da Sessao: %s"%inicial_time
    
    cursor = conecta.cursor()
     
    instability_average_sum = 0
       
    for i in range(0,len(executions)):
        sql="SELECT time, start_time, finish_time, quality, bitrate FROM dash_throughseg WHERE fk_execution=%d"%int(executions[i])
        try:
            cursor.execute(sql)
            segmentos = cursor.fetchall()
              
        except MySQLdb.Error, e:
            print "Erro: Banco nao encontrado",e
            menu = raw_input()
            os.system("clear")
            menu()
        
        k = 4
        #diference_bitrate = 0
        bitrate_sum = 0
        instability_sum = 0
        segCount=0
        
        for i in range(3,len(segmentos)):
            diference_bitrate = 0
            bitrate_sum = 0
            start_time_seg = datetime.strptime(segmentos[i][1], '%Y-%m-%dT%H:%M:%S.%fZ')
            finish_time_seg = datetime.strptime(segmentos[i][2], '%Y-%m-%dT%H:%M:%S.%fZ')
           
            if start_time_seg >= inicial_time and finish_time_seg <= final_time:
                for d in range(0, k):
                    bitrate =  int(segmentos[i - d][4]) + 100 #float(segmentos[i - d][2])/float(segmentos[i - d][3])
                    last_bitrate = int(segmentos[i - d - 1][4]) + 100 #float(segmentos[i - d - 1][2])/float(segmentos[i - d - 1][3])
                    if bitrate != last_bitrate:
                        diference_bitrate +=  abs(bitrate -last_bitrate) * abs(k - d)
                    
                for d in range(0, k):
                    bitrate_sum += (int(segmentos[i - d - 1][4]) + 100) * abs(k - d)
                
                instability = float(diference_bitrate)/float(bitrate_sum)
                instability_sum += instability
           
                #print str(deltaTime) + " " + str(instability)
                #arqLogsInstabilityTxt.write(str(deltaTime) + " " + str(instability) + "\n")   
                segCount += 1
            
        instability_average =  instability_sum/(segCount - k) 
        #arqLogsInstabilityTxt.close()
        #print "ID: %d"%int(executions[i]) 
        print "Qtde de segmentos: %d" %segCount 
        print "Instability Average: %f" %instability_average
        
        instability_average_sum += instability_average
     
    print "==================================="
    print "Instabilidade Media: %f"%(float(instability_average_sum)/len(executions))
    
           
#-------Programa Principal------    
def menu():
    
    os.system("clear");
    print "==================================="
    print "======= QoE Metrics ========"
    print "==================================="
    opcao = raw_input("Escolha opcao desejada\n\n[1] - Coletar Trocas e Amplitudes\n[2] - Coletar Stalls e Duracoes de Stalls\n[3] - Coletar Taxa media e Justica\n[4] - Coletar Instabilidade\n[5] - Coletar Popularidade\n[6]- Gerar Graficos Gerais\n[7] - Sair")
 
    try:
        opcao = int(opcao)
        if opcao<1 or opcao>7:
            os.system("clear");
            print "OPCAO INVALIDA: Verifique o valor digitado"
            time.sleep(2)
            menu()
    except:
        os.system("clear");
        print "OPCAO INVALIDA: Verifique o valor digitado"
        time.sleep(2)
        menu()
 
    if opcao == 1:
        conecta = conectaBanco()
        executions = str(raw_input("\nDigite o(s) Id(s) da(s) execucao(oes) separados por espaco: "))
        executions = map(int, executions.split())
        #coletarTrocasAmplitudes(conecta)
        coletarTaxaJustica(conecta, executions)
        coletarStallsDuracoes(conecta, executions)
        coletarInst(conecta, executions)
        coletarPopularity(conecta, executions)
        
    elif opcao == 2:
        conecta = conectaBanco()
        
 
    elif opcao == 3:
        conecta = conectaBanco()
        coletarTaxaJustica(conecta)
 
    elif opcao == 4:
        conecta = conectaBanco()
        coletarInst(conecta)
 
    elif opcao == 5:
        conecta = conectaBanco()
        coletarPopularity(conecta)
    
    elif opcao == 6:
        conecta = conectaBanco()
        gerarGraficos(conecta)
 
    elif opcao == 7:
        sys.exit()

if __name__=='__main__':
    menu()
