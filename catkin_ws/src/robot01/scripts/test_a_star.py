#!/usr/bin/env python

#import rospy
#from visualization_msgs.msg import Marker
#from visualization_msgs.msg import MarkerArray

from MapDecomposition import*
from Astar import*
from RobotPoseBr import*

def addMarker(position,r,g,b,namespace,frame_id,marker_id,markerAry):
	marker = Marker()
	marker.header.frame_id = frame_id
	marker.ns = namespace
	marker.id = marker_id
	marker.type = marker.CUBE
	marker.action = marker.ADD
	marker.pose.position.x = position[0]
	marker.pose.position.y = position[1]
	marker.pose.orientation.w = 1
	marker.scale.x = 0.1
	marker.scale.y = 0.1
	marker.scale.z = 0.2
	marker.color.r = r
	marker.color.g = g
	marker.color.b = b
	marker.color.a = 1
	markerAry.append(marker)
	return markerAry
	#self.pubMarker.publish(self.markerAry)

def get_map():
	rospy.wait_for_service('static_map')
	try:
		map_storage = rospy.ServiceProxy('static_map', GetMap)
		return map_storage()
	except rospy.ServiceException, e:
		print "Service call failed: %s"%e

def draw_markers(markerPub, markerAry):
	markerArray = MarkerArray()
	for m in markerAry:
		markerArray.markers.append(m)
	markerPub.publish(markerArray)

try:

	print "starting"
	#decomposition = MapDecomposition()
	
	print "decomposition is done"
	#robotBr = RobotPoseBr()
	mapa = get_map().map
	astar = Astar(start_point_xy = [-64.00,0.00], goal_points_xy = [[-48.0,0.0],[-52.0,.0]], grid = mapa)
	markerPathPub = rospy.Publisher('/AstarPath', MarkerArray, queue_size=1)
	#broadcaster = tf.TransformBroadcaster()
	markerAry = []
	marker_id = 0
	for i in astar.path:
		addMarker(i,0.1,1,1,i,"/map",marker_id,markerAry)
		marker_id += 1
	draw_markers(markerPathPub, markerAry)
	
except KeyboardInterrupt:
	print "Exiting"
	pass