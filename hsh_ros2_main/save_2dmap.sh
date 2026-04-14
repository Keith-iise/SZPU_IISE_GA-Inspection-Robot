source install/setup.bash
ros2 run nav2_map_server map_saver_cli -t /map -f test
# cmds=(  "ros2 run nav2_map_server map_saver_cli -t /map -f test")


# for cmd in "${cmds[@]}"
# do
# 	echo Current CMD : "$cmd"
# 	gnome-terminal -- bash -c "cd $(pwd);source install/setup.bash;$cmd;exec bash;"
# 	sleep 0.2 
# done



