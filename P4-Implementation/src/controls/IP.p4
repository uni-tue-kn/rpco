control IP(inout header_t hdr, inout ingress_metadata_t ig_md, inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md, inout ingress_intrinsic_metadata_for_tm_t ig_tm_md, in ingress_intrinsic_metadata_t ig_intr_md) {

#Random<bit<11>>() rand;
    Random<bit<14>>() rand;
    Register<bit<16>, bit<1>>(1024) pkt_counter;

    RegisterAction<bit<16>, bit<1>, bit<16>>(pkt_counter) count = {
      void apply(inout bit<16> value, out bit<16> read_value) {
        if(value > 1000) {
          value = 0;
          read_value = value;
        }
        else {
          value = value + 1;
          read_value = value;
        }
      }
    };

    action forward(PortId_t e_port) {
        ig_tm_md.ucast_egress_port = e_port;
    }

    table ip {
        key = {
            hdr.ipv4.dst_addr: lpm;
        }
        actions = {
            forward;
        }
    }

    action add_bier(bierBitmask bs) {
        hdr.bier.setValid(); // activate bier header
        hdr.bier.proto = hdr.ethernet.ether_type;
        hdr.bier.bs = bs;

        hdr.ethernet.ether_type = ETHERTYPE_BIER;


        // copy outer ip header to inner, remove outer
        hdr.ipv4_inner.setValid();
        hdr.ipv4_inner = hdr.ipv4;
        hdr.ipv4.setInvalid();
    }

    table encap_ipv4 {
        key = {
            ig_md.random_header_index: exact;
        }
        actions = {
            add_bier;
        }
        size = 18000;
    }

    apply {
        if (ip.apply().hit) {
            ig_md.random_header_index = (bit<20>) rand.get();
            if(encap_ipv4.apply().hit) {
                ig_tm_md.ucast_egress_port = RECIRCULATE_PORT2;

                bit<16> val = count.execute((bit<1>)0);

                if(val == 0) { // send to controller
                  ig_tm_md.ucast_egress_port = RECIRCULATE_PORT3;
                }
            }
        }
    }
}
