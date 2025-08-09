from lib.messages import *
from lib.crc import crc
import lib.cobs as cobs

def _send_max_packet_size():
    # Implementation for sending the maximum packet size
    pass

def _send_max_chunk_size():
    running_crc = 0
    for i in range(0, len(EXAMPLE_PROGRAM), info_response.max_chunk_size):
        chunk = EXAMPLE_PROGRAM[i : i + info_response.max_chunk_size]
        running_crc = crc(chunk, running_crc)
        chunk_response = await send_request(
            TransferChunkRequest(running_crc, chunk), TransferChunkResponse
        )
    

# Source: https://lego.github.io/spike-prime-docs/connect.html#id1
async def send_message(message: BaseMessage) -> None:
    """ serialize and pack a message, then send it to the hub"""
    print(f"Sending: {message}")
    payload = message.serialize()
    frame = cobs.pack(payload)

    # use the max_packet_size from the info response if available
    # otherwise, assume the frame is small enough to send in one packet
    packet_size = info_response.max_packet_size if info_response else len(frame)

    # send the frame in packets of packet_size
    for i in range(0, len(frame), packet_size):
        packet = frame[i : i + packet_size]
        await client.write_gatt_char(rx_char, packet, response=False)

async def send_request(message: BaseMessage, response_type: type[TMessage]) -> TMessage:
    """send a message and wait for a response of a specific type"""
    nonlocal pending_response
    pending_response = (response_type.ID, asyncio.Future())
    await send_message(message)
    return await pending_response[1]: type[TM]) -> TM    nonlocal pending_response
