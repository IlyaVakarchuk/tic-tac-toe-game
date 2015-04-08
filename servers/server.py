#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket, hashlib, threading, base64, struct, ast

class WebSocketServer:

   mainsocket = ''
   vurGame = None

   def __init__(self, ClassName, host = '', port = 9876):
      self.mainsocket = socket.socket()
      self.mainsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.mainsocket.bind((host, port))
      self.mainsocket.listen(5)
      self.vurGame = Game()
      self.serverActiveOn(ClassName)

   def serverActiveOn(self, ClassName):
      while 1:
         conn, addr = self.mainsocket.accept()
         data = conn.recv(1024)
         if 'HTTP/1.1' in data:
            print 'Connection from: ', addr
            threading.Thread(target = ClassName, args = (conn, addr, data, self.vurGame)).start()
         elif data:
            self.vurGame.parseData(data)
            print self.vurGame.userName
            print self.vurGame.board

class WebSocketItem:

   ControlFrames = {
                  'close' : 0x8,
                  'ping' : 0x9,
                  'pong' : 0xA
               }

   DataFrames = {
                  'text' : 0x81,
                  'binary' : 0x82
               }

   # Information from message header
   MessageInfo = {
                  'fin' : 0,
                  'mask' : False,
                  'opcode' : 0,
                  'length' : 0,
                  'maskarray' : None,
                  'lengtharray' : None
               }

   keypart = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
   
   # Pointer to connection
   client = ''

   # Connection addr
   addr = ''

   # Connection status
   handshakedState = False

   # Cur message parse state
   state = 1

   index = 0

   # Message from client
   receivedMessage = None

   gameItem = None

   def __init__(self, client, addr, header, gameItem):
      self.gameItem = gameItem
      self.client = client
      self.addr = addr
      self.handshaked(header)
      self.handlers()
      print 'exit'

   # Opening Handshake
   # Get header from client and send server answer
   def handshaked(self, header):

      #data = self.client.recv(1024)
      data = header
      key = self.getKey(data)

      # Encode hash (client side key + server string) by Base64
      digest = base64.b64encode(hashlib.sha1(key + self.keypart).digest())
      
      # Form answer
      shake = "HTTP/1.1 101 Switching Protocols\r\n"
      shake += "Upgrade: websocket\r\n" 
      shake += "Connection: Upgrade\r\n"
      shake += "Sec-WebSocket-Accept: %s\r\n\r\n" % (digest)
      
      # Send answer header
      self.client.send(shake)

      # Change status
      self.handshakedState = True

   def parseMessage(self, byte):
      # First message byte
      if self.state == 1:

         # Get FIN frame
         self.MessageInfo['fin'] = (byte & 0x80)

         # Get message type
         self.MessageInfo['opcode'] = (byte & 0x0F)

         self.state = 2

      # Second message byte
      elif self.state == 2:

         # Get mask
         mask = byte & 0x80
         
         # Get message length
         length = byte & 0x7F

         # Determine whether the encrypted data
         if mask == 128:
            self.MessageInfo['mask'] = True
         else:
            self.MessageInfo['mask'] = False

         # Determine length type
         if length <= 125:
            self.MessageInfo['length'] = length

            if self.MessageInfo['mask'] == True:
               self.MessageInfo['maskarray'] = bytearray()
               self.state = 5
            else: 
               self.receivedMessage = bytearray()
               self.state = 6 
         elif length == 126:
            self.MessageInfo['length'] = 126
            self.MessageInfo['lengtharray'] = bytearray()
            self.state = 3
         elif length == 127:
            self.MessageInfo['length'] = 127
            self.MessageInfo['lengtharray'] = bytearray()
            self.state = 4

      # If message length is 2 byte long
      elif self.state == 3:
         self.MessageInfo['lengtharray'].append(byte)

         if len(self.MessageInfo['lengtharray']) == 2:
            if self.MessageInfo['mask'] == True:
               self.MessageInfo['maskarray'] = bytearray()
               self.state = 5
            else:
               self.receivedMessage = bytearray()
               self.state = 6 

      # If message length is 2 byte long
      elif self.state == 4:
         self.MessageInfo['lengtharray'].append(byte)

         if len(self.MessageInfo['lengtharray']) == 8:
            if self.MessageInfo['mask'] == True:
               self.MessageInfo['maskarray'] = bytearray()
               self.state = 5
            else:
               self.receivedMessage = bytearray()
               self.state = 6 

      # Get mask data
      elif self.state == 5:
         self.MessageInfo['maskarray'].append(byte)

         if len(self.MessageInfo['maskarray']) == 4:
            self.index = 0
            self.receivedMessage = bytearray()
            self.state = 6

      # Read message
      elif self.state == 6:
         if self.MessageInfo['mask'] is True:
            # Byte decryption
            self.receivedMessage.append(byte ^ self.MessageInfo['maskarray'][self.index % 4])
         else:
            # If the byte is not encrypted
            self.receivedMessage.append(byte)

         self.index += 1      

   def sendMessage(self, message):
      answer = bytearray()

      # Determining the type of message
      # Set first byte
      if isinstance(message, str) is True:
         answer.append(self.DataFrames['text'])
      else:
         answer.append(self.DataFrames['binary'])

      tmp = 0
      length = len(message)

      # Set second byte
      if length <= 125:
         tmp |= length
         answer.append(tmp)
      elif length >= 126 and length <= 65535:
         tmp |= 126
         answer.append(tmp)
         answer.extend(struct.pack("!H", length))
      else:
         tmp |= 127
         answer.append(tmp)
         answer.extend(struct.pack("!Q", length))

      answer = answer + message
      size = len(answer)
      tosend = size
      index = 0

      # Send to client
      while tosend > 0:
         sent = self.client.send(str(answer[index:size]))
         index += sent
         tosend -= sent

   def handlers(self):
      pass

   # Get key generated by the client side
   def getKey(self, data):
      headers = {}
      lines = data.splitlines()
      for l in lines:
         parts = l.split(": ", 1)
         if len(parts) == 2:
            if parts[0] == 'Sec-WebSocket-Key':
               return parts[1]
      return headers

# Games Item
# Contains common data for all users
class Game:
   userName = []
   board = []
   gameState = 0
   tmpBoard = []

   def __init__(self):
      for i in range(3):
         self.board.append([-1] * 3)
         self.tmpBoard.append([-1] * 3)

   def parseData(self, data):
      newdata = ast.literal_eval(data)
      self.userName = newdata['players']
      self.board = newdata['board']

   def formData(self):
      data = {}
      data['players'] = self.userName
      data['board'] = self.board
      return data

   def nextStep(self, data):
      data = data.split(' ')
      self.board[int(data[0])][int(data[1])] = data[2]
      return self.curState()

   def checkBoard(self):
      if (self.board[0][0] == self.board[1][0] and  self.board[1][0] == self.board[2][0] and self.board[2][0] == self.board[0][0] and self.board[0][0] != -1) or \
      (self.board[0][0] == self.board[0][1] and  self.board[0][1] == self.board[0][2] and self.board[0][2] == self.board[0][0] and self.board[0][0] != -1) or \
      (self.board[1][0] == self.board[1][1] and  self.board[1][1] == self.board[1][2] and self.board[1][2] == self.board[1][0] and self.board[1][0] != -1) or \
      (self.board[2][0] == self.board[2][1] and  self.board[2][1] == self.board[2][2] and self.board[2][2] == self.board[2][0] and self.board[2][0] != -1) or \
      (self.board[0][1] == self.board[1][1] and  self.board[1][1] == self.board[2][1] and self.board[2][1] == self.board[0][1] and self.board[0][1] != -1) or \
      (self.board[0][0] == self.board[1][1] and  self.board[1][1] == self.board[2][2] and self.board[2][2] == self.board[0][0] and self.board[0][0] != -1) or \
      (self.board[0][2] == self.board[1][1] and  self.board[1][1] == self.board[2][0] and self.board[2][0] == self.board[0][2] and self.board[0][2] != -1) or \
      (self.board[0][2] == self.board[1][2] and  self.board[1][2] == self.board[2][2] and self.board[2][2] == self.board[0][2] and self.board[0][2] != -1):
         self.gameState = 1

   def curState(self):
      if (self.board[0][0] == self.board[1][0] and  self.board[1][0] == self.board[2][0] and self.board[2][0] == self.board[0][0] and self.board[0][0] != -1) or \
      (self.board[0][0] == self.board[0][1] and  self.board[0][1] == self.board[0][2] and self.board[0][2] == self.board[0][0] and self.board[0][0] != -1) or \
      (self.board[1][0] == self.board[1][1] and  self.board[1][1] == self.board[1][2] and self.board[1][2] == self.board[1][0] and self.board[1][0] != -1) or \
      (self.board[2][0] == self.board[2][1] and  self.board[2][1] == self.board[2][2] and self.board[2][2] == self.board[2][0] and self.board[2][0] != -1) or \
      (self.board[0][1] == self.board[1][1] and  self.board[1][1] == self.board[2][1] and self.board[2][1] == self.board[0][1] and self.board[0][1] != -1) or \
      (self.board[0][0] == self.board[1][1] and  self.board[1][1] == self.board[2][2] and self.board[2][2] == self.board[0][0] and self.board[0][0] != -1) or \
      (self.board[0][2] == self.board[1][1] and  self.board[1][1] == self.board[2][0] and self.board[2][0] == self.board[0][2] and self.board[0][2] != -1) or \
      (self.board[0][2] == self.board[1][2] and  self.board[1][2] == self.board[2][2] and self.board[2][2] == self.board[0][2] and self.board[0][2] != -1):
         return 1
      else:
       return 0

      

class Handler(WebSocketItem):

   playerNum = 0
   secondaryServers = [['', 9877], ['', 9872]]

   playerName = ''
   gameState = 0

   def synchData(self, data):
      for i in range(0, len(self.secondaryServers)):
         self.sendData(data, self.secondaryServers[i][0], self.secondaryServers[i][1])

   def sendData(self, data, host, port):
      sck = socket.socket()
      try:
         sck.connect((host, port))
      except Exception:
         pass
      else:
         sck.send(data)
      finally:
         sck.close()

   def handlers(self):

      # INIT GAME
      # First player login and wait another player
      if len(self.gameItem.userName) < 2:
         data = self.client.recv(1024)
         for byte in data:
            self.parseMessage(ord(byte))
         self.state = 1
         self.gameItem.userName.append(str(self.receivedMessage))
         self.playerName = str(self.receivedMessage)
         self.playerNum = len(self.gameItem.userName)
         self.synchData(str(self.gameItem.formData()))
         print 'My name : ' + str(self.receivedMessage) + ', I am ' + str(self.playerNum) + ' player'
         while len(self.gameItem.userName) < 2:
            pass

      
      if len(self.gameItem.userName) >= 2:
         # Select of sides
         # 0 - CROSS (Firts login player)
         # 1 - TOE (Second login player)
         if self.gameItem.board == self.gameItem.tmpBoard:
            if self.playerNum == 1:
               self.sendMessage("0")
            elif self.playerNum == 2:
               self.sendMessage("1")

            print 'GAME BEGIN'
            self.synchData(str(self.gameItem.formData()))
            tmp = str(self.gameItem.board)
            if self.playerNum == 2:
               while 1: 
                  if (tmp != str(self.gameItem.board)):
                     self.sendMessage(str(self.gameItem.board))
                     print 'in game'
                     break
         else:
            print 'NEW SERVER'
            self.sendMessage('STEP?')
            while 1:
               data = self.client.recv(1024)
               for byte in data:
                  self.parseMessage(ord(byte))
               self.state = 1
               if str(self.receivedMessage) != '1':
                  tmp = str(self.gameItem.board)
                  while 1:
                     if tmp != str(self.gameItem.board) and self.gameItem.gameState != 1:
                        self.sendMessage(str(self.gameItem.board))
                        break
                     if self.gameItem.gameState == 1:
                        self.sendMessage('GAME OVER! You LOSE!')
                        break
                  break
               else:
                  break

         while 1:
            data = self.client.recv(1024)
            for byte in data:
               self.parseMessage(ord(byte))
            self.state = 1
            print str(self.receivedMessage)
            self.gameState = self.gameItem.nextStep(str(self.receivedMessage))
            self.gameItem.checkBoard()
            self.synchData(str(self.gameItem.formData()))
            if self.gameItem.gameState == 1:
               if self.gameState == 1:
                  print ' WIN'
                  self.sendMessage('GAME OVER! You WIN!')
               else:
                  print ' standoff'
                  self.sendMessage('GAME OVER! You LOSE!')
               break;
            tmp = str(self.gameItem.board)
            while 1: 
               if tmp != str(self.gameItem.board) and self.gameItem.gameState != 1:
                     self.sendMessage(str(self.gameItem.board))
                     break
               if self.gameItem.gameState == 1:
                     print ' LOSE'
                     self.sendMessage('GAME OVER! You LOSE!')
                     break

         while 1:
            pass

WebSocketServer(Handler)