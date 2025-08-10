from spikeble import Spike

def main():

    from hub import port
    import motor, time

    # Start motor 
    motor.run(port.A, 1000)

if __name__ == "__main__":
    Spike.run(main())