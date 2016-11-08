#!/usr/bin/env python

import rospy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped
import tf
import math

class Controller:
	"""docstring for Controller"""
	def __init__(self):
		rospy.loginfo("Starting Controller")
		self.ctl_vel = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
		self.cmd_vel = Twist()
		self.laserData = LaserScan()
		self.dimensions_xyz = self.setDimensionsParam()
		self.path = None
		self.goalMapPose = [0.0,0.0]
		self.floatGoalMapPose = [0.0,0.0]
		self.goalTheta = 0.0
		self.tf = tf.TransformListener()
		self.currentMapPose = [-64.0,0.0,0.0]
		self.latestOdomPose = [0.0,0.0,0.0]
		self.blocked = False
		rospy.wait_for_message("/amcl_pose", PoseWithCovarianceStamped)
		rospy.loginfo("AMCL ready")
		rospy.Subscriber("/amcl_pose", PoseWithCovarianceStamped, self.get_amcl_pose)
		rospy.wait_for_message("/odom", Odometry)
		rospy.loginfo("odom ready")
		rospy.Subscriber("/odom", Odometry, self.get_odom)
		#rospy.Subscriber('/base_scan', LaserScan, self.detectObstacle)
		
	def set_path(self,path,floatGoal):
		self.path = path
		self.goalMapPose = self.path.pop(0)
		self.floatGoalMapPose = floatGoal

	def setDimensionsParam(self):
		rospy.set_param('/robot/dimensions_xyz', [1.0,1.0,0.25])
		return [1.0,1.0,0.25]

	def detectObstacle(self,laserScan):
		print "I am in detectObstacle"
		self.laserData = laserScan
		curAngle=laserScan.angle_min
		inc=laserScan.angle_increment
		self.blocked = False
		for range in laserScan.ranges:
			x=range*math.cos(curAngle)
			y=range*math.sin(curAngle)
			if ((abs(y)<=1.5) and (x<=self.min_range*2)):
				self.blocked = True
				print "DETECTED OBSTACLE!!!!!!!!!!!!!"
				break
			curAngle=curAngle+inc

	def get_amcl_pose(self, data):
		position = data.pose.pose.position
		orientation = data.pose.pose.orientation
		self.currentMapPose[0] = position.x
		self.currentMapPose[1] = position.y
		self.currentMapPose[2]= tf.transformations.euler_from_quaternion([0.0, 0.0, orientation.z, orientation.w])[2]
		self.goalTheta = math.atan2(self.goalMapPose[1] - self.currentMapPose[1],
									self.goalMapPose[0] - self.currentMapPose[0])

	def get_odom(self, data):
		position = data.pose.pose.position
		orientation = data.pose.pose.orientation
		self.currentMapPose[0] = self.currentMapPose[0] + (position.x - self.latestOdomPose[0])
		self.currentMapPose[1] = self.currentMapPose[1] + (position.y - self.latestOdomPose[1])
		euler_yaw = tf.transformations.euler_from_quaternion([0.0, 0.0, orientation.z, orientation.w])[2]
		self.currentMapPose[2] = self.currentMapPose[2] + (euler_yaw - self.latestOdomPose[2])
		self.latestOdomPose[0] = position.x
		self.latestOdomPose[1] = position.y
		self.latestOdomPose[2] = euler_yaw
		self.goalTheta = math.atan2(self.goalMapPose[1] - self.currentMapPose[1],
									self.goalMapPose[0] - self.currentMapPose[0])
		
	def drive(self):
		if (not self.blocked):
			print self.currentMapPose
			print self.goalMapPose
			if (abs(self.goalMapPose[0]-self.currentMapPose[0])>0.5 or abs(self.goalMapPose[1]-self.currentMapPose[1])>0.5):
				self.cmd_vel.angular.z = self.adjust_rotation(self.goalTheta-self.currentMapPose[2])
				if abs(self.cmd_vel.angular.z) > 0.8:
					print "setting up direction"
					self.cmd_vel.linear.x = 0.0
				elif abs(self.cmd_vel.angular.z) > 0.5:
					print "creeping speed"
					self.cmd_vel.linear.x = 0.05
				elif abs(self.cmd_vel.angular.z) > 0.3:
					self.cmd_vel.linear.x = 0.1
				elif abs(self.cmd_vel.angular.z) > 0.1:
					self.cmd_vel.linear.x = 0.4
				else:
					print "Rotation is small: ", self.cmd_vel.angular.z
					self.cmd_vel.linear.x = 2
			else:
				print "point reached"
				self.goalMapPose = self.path.pop(0)
				self.goalTheta = math.atan2(self.goalMapPose[1] - self.currentMapPose[1],
									self.goalMapPose[0] - self.currentMapPose[0])
				self.cmd_vel.angular.z = 0.0
				self.cmd_vel.linear.x = 0.0
		else:
			print "robot is blocked"
			self.cmd_vel.angular.z = 0.5
			self.cmd_vel.linear.x = 0.0

		self.ctl_vel.publish(self.cmd_vel)
	
	def adjust_rotation(self, theta):
		while theta <= math.pi:
			theta += 2.0*math.pi
		while theta > math.pi:
			theta -= 2.0*math.pi
		return theta