import socket
import struct
import math
import time
import threading

import rasterizer

UDP_IP="192.168.23.37"
#UDP_IP="192.168.23.118"
LED_UDP_PORT=13664
SYNC_RCV_UDP_PORT=13665
SYNC_SEND_UDP_PORT=13666

SYNC_MES=struct.pack("B", 0)

ON_MESSAGE=struct.pack("B", 255)

print "rcv target IP:", UDP_IP, "port ", SYNC_RCV_UDP_PORT
print "send target IP:", UDP_IP, "port ", SYNC_SEND_UDP_PORT


sync_rcv_sock = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
sync_rcv_sock.bind( (UDP_IP,SYNC_RCV_UDP_PORT) )

sync_send_sock = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP

led_send_sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) # UDP


class Synchronizer(threading.Thread):

	def run(self):
		self.isrun = True
		while self.isrun:
			self.dir = wait_for_direction_change()
			if self.dir == 0:
				self.dir = 1
			else:
				self.dir = 0
			t0_previous = getattr(self, "t0", None)
			self.t0 = time.time()
			if t0_previous:
				#try:
				#	self.duration = (self.duration + self.t0 - t0_previous) / 2
				#except AttributeError:
				#	self.duration = self.t0 - t0_previous
				self.duration = self.t0 - t0_previous
				self.tick = self.duration / 128.0
				time.sleep(self.duration * 0.9)
			else:
				time.sleep(0.1)

	def stop(self):
		self.isrun = False


def get_direction_from_saw_server():
	data = None
	while data is None:
		data, addr = sync_rcv_sock.recvfrom( 1 ) # buffer size is 1024 bytes	
#		print "\nByte Length of Message :", len(data) ,"\n"
#		print "Message Data :", struct.unpack("b",data) ,"\n"
	return struct.unpack("B",data)

		
def wait_for_direction_change():
	direction = get_direction_from_saw_server()
	new_direction = direction	
	while new_direction == direction:
		new_direction =  get_direction_from_saw_server()
	return new_direction	
	

def measure_half_swing_time():
	"""This Method calculates the duration of one saw swing"""	
	wait_for_direction_change()
	start = time.time()
	wait_for_direction_change()
	end = time.time()
	print "diff: ", end - start
	return end - start


def send_byte( b ):
	#if b > 255:
	#	b = 255
	#print "b: ",b
	ON_MESSAGE = struct.pack("B", b)
	#print "send: ", ON_MESSAGE
	led_send_sock.sendto( ON_MESSAGE, (UDP_IP, LED_UDP_PORT) )


sync_send_sock.sendto( SYNC_MES, (UDP_IP, SYNC_SEND_UDP_PORT) )

raster_text = rasterizer.rasterize("t g i f")
raster_text.reverse()
column_count = len(raster_text)
print "raster_text", raster_text


# Main

synchronizer = Synchronizer()
synchronizer.start()

try:
	while not getattr(synchronizer, "tick", None):
		time.sleep(0.1)
	while True:
			print "duration ", synchronizer.duration
			delta = (time.time() - synchronizer.t0) / synchronizer.duration * 1.5
			print "delta ", delta, "d/t ", (delta / synchronizer.tick)
			column = int(math.floor(delta / synchronizer.tick))
			#if getattr(synchronizer, "dir", None) and synchronizer.dir == 1:
			#	raster_text.reverse()	
			#print "COLUMN", column, "LENGTH", column_count
			if column < column_count:
				send_byte(raster_text[column])
except KeyboardInterrupt:
	synchronizer.stop()
	raise
