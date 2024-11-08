from rfid.reader import Reader
from rfid.transport import Transport, SerialTransport
from rfid.response import ResponseInventory
from rfid.reader_settings import (
    Antenna,
    BaudRate,
    ReaderSettings,
    RfidProtocol,
    WorkMode,
    OutputInterface,
    Wiegand,
    WiegandProtocol,
    WiegandByteFirstType,
    MemoryBank,
    Frequency,
    Session,
    REGION_MALAYSIA,
    AnswerModeInventoryParameter,
    StopAfter,
)
from rfid.status import InventoryStatus
from rfid.utils import calculate_rssi
import time
import datetime
import csv
import os
from typing import Iterator

print("Starting RFID reader...")

print(SerialTransport.scan())


def log(message: str) -> None:
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

PORTS: list[str] = SerialTransport.scan()
log(f"Ports: {PORTS}")

PORT: str = SerialTransport.scan()[0]
log(f"Port: {PORT}")

TRANSPORT: SerialTransport = SerialTransport(
    serial_port=PORT, baud_rate=BaudRate.BPS_115200, timeout=1
)
log(f"Transport: {TRANSPORT}")

READER: Reader = Reader(TRANSPORT)
log("Reader Initialized")

wiegand = Wiegand(
    is_open=False,
    byte_first_type=WiegandByteFirstType.LOW_BYTE_FIRST,
    protocol=WiegandProtocol.WG_26,
)

antenna = Antenna(
    ant_1=True,
    ant_2=False,
    ant_3=False,
    ant_4=False,
    ant_5=False,
    ant_6=False,
    ant_7=False,
    ant_8=False,
)

frequency = Frequency(
    region=REGION_MALAYSIA,
    min_frequency=920.00,
    max_frequency=925.00,
)


READER.set_reader_settings(
    ReaderSettings(
        address=0,
        rfid_protocol=RfidProtocol.ISO_18000_6C,
        work_mode=WorkMode.ACTIVE_MODE,
        output_interface=OutputInterface.USB,
        baud_rate=BaudRate.BPS_115200,
        wiegand=wiegand,
        antenna=antenna,
        frequency=frequency,
        power=30,  # max RC4 dbm
        output_memory_bank=MemoryBank.EPC,
        q_value=4,
        session=Session.SESSION_0,
        output_start_address=0,
        output_length=12,
        filter_time=0,
        trigger_time=3,
        buzzer_time=True,
        inventory_interval=100,
    )
)

# run the reader
response: Iterator[ResponseInventory] | None = READER.start_inventory(
                work_mode=WorkMode.ANSWER_MODE,
                answer_mode_inventory_parameter=(
                    AnswerModeInventoryParameter(
                        stop_after=StopAfter.NUMBER,
                        value=10,
                    )
                ),
            )
i = 0

rssi_value=[]
response_value=[]
with open('data.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    if os.stat('data.csv').st_size == 0:
        csvwriter.writerow(["RSSI", "Response Time (µs)","Jarak (M)"])
      # Header kolom
    start_time = time.time()  # Catat waktu mulai program
    while time.time() - start_time < 10: 
        for res in response:
            i+=1
            waktu_mulai = time.time()  # Catat waktu mulai memproses respons
            print()
            print(f"({i}).InventoryThread() > run() > res: {res}")

            if res is None:
                continue  # Lewati respons None

            if res.status == InventoryStatus.SUCCESS and res.tag:
                rssi = calculate_rssi(res.tag.rssi)
                nilai_rssi= int(rssi)
                response_time_micro = (time.time() - waktu_mulai) * 1000000  # Hitung waktu respons dalam mikrodetik
                print(
                    f"RSSI:{nilai_rssi:d} - Response Time: {response_time_micro:.2f}µs"
                )
            

                rssi_value.append(nilai_rssi)
                response_value.append(response_time_micro)
                Jarak = 1.5 
                csvwriter.writerow([nilai_rssi, response_time_micro,Jarak])  # Tulis data ke CSV


            if res.status == InventoryStatus.NO_COUNT_LABEL and READER.work_mode == WorkMode.ANSWER_MODE:
                break
            if time.time() - start_time >= 10:
                break


READER.stop_inventory()
READER.close()