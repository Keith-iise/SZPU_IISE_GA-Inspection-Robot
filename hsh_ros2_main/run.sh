
cmds=(  
# "ros2 launch bringup real_bringup.launch.py     world:=test     mode:=nav      lio:=fastlio\
#      lio_rviz:=false     nav_rviz:=True     use_sim_time:=false    localization:=icp"
# "ros2 launch serial_node serial_comm.launch.py "
"ros2 run model_communication communication_node "
# "ros2 launch multi_waypoint_navigator navigator.launch.py"
# "ros2 launch waypoint_saver waypoint_saver.launch.py"
"ros2 run expression_show show_node "
	 )

#"ros2 launch pcd2pgm pcd2pgm.launch.py"

# "ros2 launch octomap_server2 octomap_server_launch.py"
for cmd in "${cmds[@]}"
do
	echo Current CMD : "$cmd"
	gnome-terminal -- bash -c "cd $(pwd);source install/setup.bash;$cmd;exec bash;"
	sleep 0.2 
done
