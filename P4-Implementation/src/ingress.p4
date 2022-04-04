#include "controls/IP.p4"

#include "controls/ARP.p4"

#include "controls/BIER.p4"


control ingress(
    inout header_t hdr,
    inout ingress_metadata_t ig_md, in ingress_intrinsic_metadata_t ig_intr_md, in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
    inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
    inout ingress_intrinsic_metadata_for_tm_t ig_tm_md) {

    IP() ip_c;
    ARP() arp_c;
    BIER() bier_c;

    // BIER-FRR Test
    Register<bit<32>, bit<1>>(1024) port_indicator;

    RegisterAction<bit<32>, bit<1>, bit<32>>(port_indicator) read_port = {
      void apply(inout bit<32> value, out bit<32> read_value) {
        value = value;
        read_value = value;
      }
    };

    RegisterAction<bit<32>, bit<1>, bit<32>>(port_indicator) set_port = {
      void apply(inout bit<32> value, out bit<32> read_value) {
        value = value | ig_md.port_down_bit;
        read_value = value;
      }
    };

    RegisterAction<bit<32>, bit<1>, bit<32>>(port_indicator) del_port = {
      void apply(inout bit<32> value, out bit<32> read_value) {
        value = value & ig_md.port_down_bit;
        read_value = value;
      }
    };



    apply {
      if(hdr.bier.isValid()) {
        bit<32> bitvector = set_port.execute(0);
      }
      else {
        bit<32> bitvector = del_port.execute(0);
      }
      if(ig_intr_md.ingress_port == RECIRCULATE_PORT3) {
        ig_md.mirror_session = 1002;

        hdr.bier_md.setValid();
        hdr.bier_md.bs = hdr.bier.bs;

        ig_dprsr_md.mirror_type = 1;

        ig_tm_md.ucast_egress_port = CPU_PORT;
      }
      else if(ig_intr_md.ingress_port == RECIRCULATE_PORT1) {

        // clone to second recirc port for bier processing
        ig_md.mirror_session = 1002;

        // activate cloning with bier_md header
        ig_dprsr_md.mirror_type = 1;

        // send to monitor port
       ig_tm_md.ucast_egress_port = 184;

       hdr.bier_md.setValid();
       hdr.bier_md.bs = hdr.bier.bs;

       hdr.bier.setInvalid();

       hdr.ethernet.ether_type = 0x080;


      }
      else {
        if (hdr.ethernet.ether_type == ETHERTYPE_IPV4) {
            ip_c.apply(hdr, ig_md, ig_dprsr_md, ig_tm_md, ig_intr_md);
        }
        else if (hdr.ethernet.ether_type == TYPE_ARP) {
            arp_c.apply(hdr, ig_intr_md, ig_tm_md);
        }
        else if (hdr.ethernet.ether_type == ETHERTYPE_BIER) {
#ig_tm_md.ucast_egress_port = 184;
          bier_c.apply(hdr, ig_md, ig_tm_md, ig_dprsr_md);
        }
      }
    }
}
