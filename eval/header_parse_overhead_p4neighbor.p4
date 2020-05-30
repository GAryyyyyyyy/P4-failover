#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
#define MAX_HOPS 32
#define MAX_PORTS 128
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<4> backup_length_t;
typedef bit<15> bp_hop_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}
//recover
header recoveryPath_t {
    bit<1>    bos;
    bit<15>   edge;
}
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}
struct metadata{
    bit<1>  cur_bos;
    bit<15>  out_edge;
}


struct headers {
    recoveryPath_t[MAX_HOPS] recoveryPath;
    ethernet_t   ethernet;
    ipv4_t       ipv4;
}
/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    state start {
        transition parse_myRecoveryPath;
    }
    state parse_myRecoveryPath {
        packet.extract(hdr.recoveryPath.next);
        transition select(hdr.recoveryPath.last.bos) {
            1: parse_ethernet;
            default: parse_myRecoveryPath;
        }
    }
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }
}
/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop(standard_metadata);
    }
    
    action recoveryPath_nhop() {
        meta.out_edge = hdr.recoveryPath[0].edge;
        meta.cur_bos = hdr.recoveryPath[0].bos;
        hdr.recoveryPath.pop_front(1);
    }

    action recovery_forward(egressSpec_t port) {
        standard_metadata.egress_spec = port;
    }

    table edge_to_port {
        key = {
            meta.out_edge: exact;
        }
        actions = {
            recovery_forward;
            drop;
        }
        default_action = drop();
        const entries = {
            (1): recovery_forward(56);
        }
    }

    action update_ttl(){
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action update_mac_addr(macAddr_t dstAddr) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
    }

    table port_to_mac {
        key = {
            standard_metadata.egress_spec: exact;
        }
        actions = {
            update_mac_addr;
        }
        const entries = {
            (56): update_mac_addr(0x123456789ABC);
        }
    }

    apply {
        recoveryPath_nhop();
        edge_to_port.apply();
        update_ttl();
        port_to_mac.apply();
    }
}

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
    apply {  
        update_checksum(
	        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	          hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/
control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.recoveryPath);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
    }
}
/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;