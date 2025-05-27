from naps import *

class StreamPacketBuffer(Elaboratable):
    """Buffers an entire packet to make sure it can be transferred without a stall and measures the length of the packet (in bytes).
    If the packet does not fit into the buffer, it is dropped.
    """

    def __init__(self, input, buffer_size=2048):
        self.buffer_size = buffer_size
        self.input = input
        self.output = PacketizedStream(32, name="stream_packet_buffer_output")
        self.output.length = Signal(16)

        self.dropped_too_long = StatusSignal(16)

    def elaborate(self, platform):
        m = Module()

        data_fifo_input = self.input.clone()
        data_fifo = m.submodules.data_fifo = BufferedSyncStreamFIFO(data_fifo_input, self.buffer_size, output_stream_name="data_fifo_out")

        length_fifo_input = BasicStream(range(self.buffer_size + 1))
        length_fifo = m.submodules.length_fifo = BufferedSyncStreamFIFO(length_fifo_input, 8, output_stream_name="length_fifo_out")

        # input
        m.d.comb += self.input.ready.eq(data_fifo_input.ready & length_fifo_input.ready)
        m.d.comb += data_fifo_input.valid.eq(self.input.valid & self.input.ready)
        m.d.comb += data_fifo_input.last.eq(self.input.last)
        m.d.comb += data_fifo_input.payload.eq(self.input.payload)
        
        input_counter = Signal(range(self.buffer_size))
        overflow = Signal()
        with m.If(self.input.ready & self.input.valid):
            with m.If(overflow):
                with m.If(self.input.last):
                    m.d.sync += overflow.eq(0)
                    m.d.sync += input_counter.eq(0)
            with m.Elif(self.input.last):
                m.d.sync += input_counter.eq(0)
                m.d.comb += length_fifo_input.payload.eq(input_counter)
                m.d.comb += length_fifo_input.valid.eq(1)
            with m.Elif((input_counter == self.buffer_size - 1)):
                m.d.comb += length_fifo_input.payload.eq(input_counter)
                m.d.comb += length_fifo_input.valid.eq(1)
                m.d.sync += overflow.eq(1)
                m.d.sync += self.dropped_too_long.eq(self.dropped_too_long+1)
            with m.Else():
                m.d.sync += input_counter.eq(input_counter + 1)

        # output
        skip = Signal()
        with m.If(length_fifo.output.valid & data_fifo.output.valid):
            with m.If(skip):
                m.d.comb += data_fifo.output.ready.eq(1)
                with m.If(data_fifo.output.valid & data_fifo.output.last):
                    m.d.sync += skip.eq(0)
                    m.d.comb += length_fifo.output.ready.eq(1)
            with m.Elif(length_fifo.output.payload == self.buffer_size - 1):
                m.d.sync += skip.eq(1)
            with m.Else():
                m.d.comb += self.output.valid.eq(1)
                m.d.comb += data_fifo.output.ready.eq(self.output.ready)
                m.d.comb += self.output.last.eq(data_fifo.output.last)
                m.d.comb += length_fifo.output.ready.eq(self.output.ready & data_fifo.output.last)
                m.d.comb += self.output.payload.eq(data_fifo.output.payload)
                m.d.comb += self.output.length.eq((length_fifo.output.payload + 1) * (len(self.input.payload) // 8))

        return m
