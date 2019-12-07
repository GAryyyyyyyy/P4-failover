import grpc
import os
import sys
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

    
if __name__ == '__main__':
    p4info_file_path = './build/simple_recovery.p4.p4info.txt'
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    try:
        s = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
        )
        s.MasterArbitrationUpdate()
        # table_entry = p4info_helper.buildTableEntry(
        #     table_name="MyIngress.ipv4_lpm",
        #     match_fields={
        #         "hdr.ipv4.dstAddr": ("10.0.2.2", 32)
        #     },
        #     action_name="MyIngress.try_ipv4_forward",
        #     action_params={
        #         "port": 3,
        #     }
        # )
        # s.ModifyTableEntry(table_entry)
        for response in s.ReadRegisters(p4info_helper.get_registers_id("MyIngress.all_ports_status")):
            for entity in response.entities:
                registers = entity.register_entry
                print registers
    except KeyboardInterrupt:
        print " Shutting down."
    except grpc.RpcError as e:
        printGrpcError(e)