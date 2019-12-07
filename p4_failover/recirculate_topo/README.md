# recirculate test topo
This topology is used to test whether port_fault in failover process can be handled correctly!

bos_1_case sub-directory shows that when bos==1 and out port fault, we can handle this situation correctly.

current directory show that when bos != 1 and out port fault, we can handle this situation correctly.

In conclusion, with the help of primitive recirculate, although we may encounter port fault when we are doing failover, we can handle this situation correctly!
