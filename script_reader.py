#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-

"""
 @file script_reader.py
 @brief ModuleDescription
 @date $Date$


"""
import sys
import time
sys.path.append(".")

# Import RTM module
import RTC
import OpenRTM_aist

import json
import requests
import pyaudio
import shutil
import wave
import numpy as np
import math

# Import Service implementation class
# <rtc-template block="service_impl">

# </rtc-template>

# Import Service stub modules
# <rtc-template block="consumer_import">
# </rtc-template>


# This module's spesification
# <rtc-template block="module_spec">
script_reader_spec = ["implementation_id", "script_reader", 
		 "type_name",		 "script_reader", 
		 "description",	   "ModuleDescription", 
		 "version",		   "1.0.0", 
		 "vendor",			"Takahiro Horikawa", 
		 "category",		  "Development", 
		 "activity_type",	 "STATIC", 
		 "max_instance",	  "1", 
		 "language",		  "Python", 
		 "lang_type",		 "SCRIPT",
		 "conf.default.script_file", "/tmp/script.txt",
		 "conf.__widget__.script_file", "text",
		 ""]
# </rtc-template>

##
# @class script_reader
# @brief ModuleDescription
# 
# 
class script_reader(OpenRTM_aist.DataFlowComponentBase):
	
	##
	# @brief constructor
	# @param manager Maneger Object
	# 
	def __init__(self, manager):
		OpenRTM_aist.DataFlowComponentBase.__init__(self, manager)

		self._d_servo_robot1 = RTC.TimedVector2D(RTC.Time(0,0),0)
		"""
		"""
		self._servo_robot1Out = OpenRTM_aist.OutPort("servo_robot1", self._d_servo_robot1)
		self._d_servo_robot2 = RTC.TimedVector2D(RTC.Time(0,0),0)
		"""
		"""
		self._servo_robot2Out = OpenRTM_aist.OutPort("servo_robot2", self._d_servo_robot2)


		


		# initialize of configuration-data.
		# <rtc-template block="init_conf_param">
		"""
		
		 - Name:  script_file
		 - DefaultValue: /tmp/script.txt
		"""
		self._script_file = ['/tmp/script.txt']
		
		# </rtc-template>


		 
	##
	#
	# The initialize action (on CREATED->ALIVE transition)
	# formaer rtc_init_entry() 
	# 
	# @return RTC::ReturnCode_t
	# 
	#
	def onInitialize(self):
		# Bind variables and configuration variable
		self.bindParameter("script_file", self._script_file, "/tmp/script.txt")
		
		# Set InPort buffers
		
		# Set OutPort buffers
		self.addOutPort("servo_robot1",self._servo_robot1Out)
		self.addOutPort("servo_robot2",self._servo_robot2Out)
		
		# Set service provider to Ports
		
		# Set service consumers to Ports
		
		# Set CORBA Service Ports
		
		return RTC.RTC_OK
	
	#	##
	#	# 
	#	# The finalize action (on ALIVE->END transition)
	#	# formaer rtc_exiting_entry()
	#	# 
	#	# @return RTC::ReturnCode_t
	#
	#	# 
	#def onFinalize(self):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The startup action when ExecutionContext startup
	#	# former rtc_starting_entry()
	#	# 
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	def onStartup(self, ec_id):
		print "load script file"
		f = open(self._script_file[0])
		self.script_data = json.load(f)
		print str(self.script_data)

		self.audio = pyaudio.PyAudio()
		self.onActivated(1)
		return RTC.RTC_OK
	
	#	##
	#	#
	#	# The shutdown action when ExecutionContext stop
	#	# former rtc_stopping_entry()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	#def onShutdown(self, ec_id):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The activated action (Active state entry action)
	#	# former rtc_active_entry()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	# 
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	def onActivated(self, ec_id):
		print "onActivated"
		for line in self.script_data:
			self.speak(line["audio_url"])
			if line["robot_id"] == 1:
				pass
			elif line["robot_id"] == 2:
				pass
			else:
				print "invalid robot id:" + str(line.robot_id)
		return RTC.RTC_OK
	
	def speak(self, audio_url):
		cache_file = "cache.wav"
		res = requests.get(audio_url, stream=True)
		with open(cache_file, "wb") as fp:
			shutil.copyfileobj(res.raw, fp)

		wf = wave.open(cache_file, "r")
		sampleRate = wf.getframerate()
		channels = wf.getnchannels()
		stream = self.audio.open(
			format = self.audio.get_format_from_width(wf.getsampwidth()),
			channels = channels,
			rate = sampleRate,
			output = True)

		amp  = (2**8) ** wf.getsampwidth() / 2
		print "nframe=%d" % wf.getnframes()
		buffer = wf.readframes(wf.getnframes())
		data = np.frombuffer(buffer, dtype="int16")
		# normalize
		data = data / float(amp)
		print "len=%d" % len(data)
		# for i in range(len(data)/2):
		# 	d = data[2*i] * 256 + data[2*i + 1]
		# 	print str(d)
		threshold = 0.05
		minSilentDurationInSec = 0.2
		minSilentSamples = minSilentDurationInSec * sampleRate

		start = 0
		index = 0
		lowCount = 0
		silentPart = []
		noisyPart = []

		for i in range(len(data)):
			if math.fabs(data[i]) < threshold:
				if lowCount == 0:
					start = index
				lowCount = lowCount + 1
			else:
				if lowCount > minSilentSamples:
					silentPart.append(start)
					silentPart.append(index)
				lowCount = 0
			index = index + 1

		if lowCount > minSilentSamples:
			silentPart.append(start)
			silentPart.append(index - 1)

		offset = 0
		for i in range(len(silentPart) / 2):
			if silentPart[2*i] > offset:
				noisyPart.append(offset / float(sampleRate))
				noisyPart.append(silentPart[2*i] / float(sampleRate))
			offset = silentPart[2*i + 1]

		if offset < index - 1:
			noisyPart.append(offset / float(sampleRate))
			noisyPart.append((index - 1) / float(sampleRate))

		noisyPart = map(lambda t: 1000*t, noisyPart)
		print str(noisyPart)

		# stream.write(buffer)
		# stream.close()
		self.audio.terminate()

		pass

	#	##
	#	#
	#	# The deactivated action (Active state exit action)
	#	# former rtc_active_exit()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	#def onDeactivated(self, ec_id):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The execution action that is invoked periodically
	#	# former rtc_active_do()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	def onExecute(self, ec_id):
		print "onExecute"
		self._d_servo_robot1.data = RTC.Vector2D(4, 80)
		OpenRTM_aist.setTimestamp(self._d_servo_robot1)
		self._servo_robot1Out.write()
		return RTC.RTC_OK
	
	#	##
	#	#
	#	# The aborting action when main logic error occurred.
	#	# former rtc_aborting_entry()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	#def onAborting(self, ec_id):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The error action in ERROR state
	#	# former rtc_error_do()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	#def onError(self, ec_id):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The reset action that is invoked resetting
	#	# This is same but different the former rtc_init_entry()
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	#def onReset(self, ec_id):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The state update action that is invoked after onExecute() action
	#	# no corresponding operation exists in OpenRTm-aist-0.2.0
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#

	#	#
	#def onStateUpdate(self, ec_id):
	#
	#	return RTC.RTC_OK
	
	#	##
	#	#
	#	# The action that is invoked when execution context's rate is changed
	#	# no corresponding operation exists in OpenRTm-aist-0.2.0
	#	#
	#	# @param ec_id target ExecutionContext Id
	#	#
	#	# @return RTC::ReturnCode_t
	#	#
	#	#
	#def onRateChanged(self, ec_id):
	#
	#	return RTC.RTC_OK
	



def script_readerInit(manager):
	profile = OpenRTM_aist.Properties(defaults_str=script_reader_spec)
	manager.registerFactory(profile,
							script_reader,
							OpenRTM_aist.Delete)

def MyModuleInit(manager):
	script_readerInit(manager)

	# Create a component
	comp = manager.createComponent("script_reader")

def main():
	mgr = OpenRTM_aist.Manager.init(sys.argv)
	mgr.setModuleInitProc(MyModuleInit)
	mgr.activateManager()
	mgr.runManager()

if __name__ == "__main__":
	main()

