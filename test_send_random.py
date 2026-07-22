#!/usr/bin/env python3
"""
测试程序：向 /dev/tnt0 发送 "x,x,x" 格式的随机数字。
在另一端用 cat /dev/tnt1 或串口工具接收。
"""

import random
import serial
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="向虚拟串口发送随机数字")
    parser.add_argument("--port", default="/dev/tnt0", help="发送端口 (默认: /dev/tnt0)")
    parser.add_argument("--baudrate", type=int, default=115200, help="波特率 (默认: 115200)")
    parser.add_argument("--interval", type=float, default=0.5, help="发送间隔秒数 (默认: 0.5)")
    parser.add_argument("--count", type=int, default=0, help="发送次数，0=无限 (默认: 0)")
    parser.add_argument("--min", type=int, default=0, dest="min_val", help="随机数最小值 (默认: 0)")
    parser.add_argument("--max", type=int, default=100, dest="max_val", help="随机数最大值 (默认: 100)")
    parser.add_argument("--num-count", type=int, default=3, help="每行随机数个数 (默认: 3)")
    args = parser.parse_args()

    print(f"打开端口: {args.port}, 波特率: {args.baudrate}")
    ser = serial.Serial(args.port, args.baudrate, timeout=1)

    sent = 0
    try:
        while args.count == 0 or sent < args.count:
            # 生成 x,x,x 格式的随机数
            values = [str(random.randint(args.min_val, args.max_val)) for _ in range(args.num_count)]
            line = ",".join(values) + "\n"

            ser.write(line.encode("utf-8"))
            ser.flush()

            sent += 1
            print(f"[{sent}] 发送: {line.rstrip()}")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        ser.close()
        print(f"已发送 {sent} 条，端口已关闭。")


if __name__ == "__main__":
    main()
