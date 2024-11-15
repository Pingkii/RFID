import datetime
import os
import time
import csv

from rfid.reader import Reader
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
from rfid.transport import SerialTransport
from rfid.utils import calculate_rssi
from typing import Iterator

def log(message: str) -> None:
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

FREQUENCY_LIST: list[float] = [919.5,919.6,919.7,919.8,919.9, 920.0,920.1,920.2,920.3,920.4, 920.5,920.6,920.7,920.8,920.9, 921.0,921.1,921.2,921.3,921.4, 921.5,921.6,921.7,921.8,921.9, 922.0,922.1,922.2,922.3,922.4, 922.5]

PORTS: list[str] = SerialTransport.scan()
log(f"Ports: {PORTS}")

PORT: str = SerialTransport.scan()[1]
log(f"Port: {PORT}")

TRANSPORT: SerialTransport = SerialTransport(
    serial_port=PORT, baud_rate=BaudRate.BPS_115200, timeout=1
)
log(f"Transport: {TRANSPORT}")

READER: Reader = Reader(TRANSPORT)
log("Reader Initialized")

try:
    while True:
        input("Press Enter to start reading RSSI...")
        log("Starting")

        # Create a CSV file to store the data
        csv_file = open('Jarak_dataset.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([ 'RSSI (dBm)', 'Response Time (µs)','Jarak (M)'])  # Write header row

        average_rssi_list: list[float] = []
        for frequency_index, frequency_value in enumerate(FREQUENCY_LIST, start=1):
            log(f"Frequency {frequency_index}: {frequency_value} MHz")
            time.sleep(0.5)

            READER.set_reader_settings(
                ReaderSettings(
                    address=0,
                    rfid_protocol=RfidProtocol.ISO_18000_6C,
                    work_mode=WorkMode.ACTIVE_MODE,
                    output_interface=OutputInterface.USB,
                    baud_rate=BaudRate.BPS_115200,
                    wiegand=Wiegand(
                        is_open=False,
                        byte_first_type=WiegandByteFirstType.LOW_BYTE_FIRST,
                        protocol=WiegandProtocol.WG_26,
                    ),
                    antenna=Antenna(
                        ant_1=True,
                        ant_2=False,
                        ant_3=False,
                        ant_4=False,
                        ant_5=False,
                        ant_6=False,
                        ant_7=False,
                        ant_8=False,
                    ),
                    frequency=Frequency(
                        region=REGION_MALAYSIA,
                        min_frequency=frequency_value,
                        max_frequency=frequency_value,
                    ),
                    power=30,
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

            response: Iterator[ResponseInventory] | None = READER.start_inventory(
                work_mode=WorkMode.ANSWER_MODE,
                answer_mode_inventory_parameter=(
                    AnswerModeInventoryParameter(
                        stop_after=StopAfter.NUMBER,
                        value=10,
                    )
                ),
            )

            count: int = 1
            rssi_list: list[int] = []
            response_time_list: list[float] = []
            try:
                for res in response:
                    print()

                    

                    if res is None:
                        continue

                    if res.status == InventoryStatus.SUCCESS and res.tag:
                        start_time = time.time()
                        rssi_value: int = int(
                            str(calculate_rssi(res.tag.rssi))[0:3]
                        )
                        nilai_rssi = int(rssi_value)

                        
                        print(f"Frequency {frequency_index} RSSI {count}: {nilai_rssi} dBm")

                        rssi_list.append(nilai_rssi)
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000000 
                        print(f"Response Time: {response_time} ms")
                        response_time_list.append(response_time)

                        count += 1
                        if count > 10:
                            break

                    if (
                        res.status == InventoryStatus.NO_COUNT_LABEL
                        and READER.work_mode == WorkMode.ANSWER_MODE
                    ):
                        break

                    time.sleep(0.1)

            except:
                
                print(f"Frequency {frequency_index} RSSI {count}: Read Error")

            READER.stop_inventory()

            print()
            log(f"Frequency {frequency_index}: {frequency_value} MHz")
            for rssi_index, nilai_rssi in enumerate(rssi_list, start=1):
                
                print(f"RSSI {rssi_index}: {nilai_rssi} dBm")

            average_rssi: float = sum(rssi_list) / len(rssi_list)
            average_rssi_list.append(average_rssi)

            time.sleep(0.5)
            
            print(f"Average RSSI: {average_rssi} dBm")

            # Calculate average response time for the frequency
            average_response_time = sum(response_time_list) / len(response_time_list)
            
            print(f"Average Response Time: {average_response_time} ms")

            jarak = 0
            # Write average RSSI and response time to the CSV file
            csv_writer.writerow([average_rssi, average_response_time,jarak])
            print(f"Jarak Sebenarnya : {jarak}")

            print()


        log("RSSI Summary Of All Frequencies")
        for average_rssi_index, average_rssi_value in enumerate(
            average_rssi_list, start=1
        ):
            print(
                f"Frequency {average_rssi_index} ({FREQUENCY_LIST[average_rssi_index-1]} MHz) Average RSSI: {average_rssi_value} dBm"
            )
        jarak += 0.5

        # Close the CSV file after writing all data
        csv_file.close()

except KeyboardInterrupt:
    pass

finally:
    READER.close()