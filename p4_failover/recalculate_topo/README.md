# recalculate test topo
This topology is used to test whether back up path recalculation can work correctly!

When edge e become unavailable, controller will recalculate back up path for those back up path which go through edge e. This mechanism will ensure that we will not encounter infinite loops in the process of failover. 
