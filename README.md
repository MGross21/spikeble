<h1 align="center">
    <img src="https://raw.githubusercontent.com/MGross21/spikeble/main/assets/spikeble_logo.png" alt="spikeble logo" width="500" />
</h1>
<p align="center">
    <sub>(pronounced "spike-able")</sub>
    <br>
    <img src="https://raw.githubusercontent.com/MGross21/spikeble/main/assets/lego_spike.png" alt="Lego Spike" width="500" />
</p>

## Installation

```bash
pip install git+https://github.com/MGross21/spikeble.git
```

> **⚠️ Warning:**  
> It is **highly recommended** to install and use this library within a Python virtual environment. Installing `spikeble` will expose all MicroPython modules (such as `app`, `color`, `color_matrix`, `color_sensor`, `device`, `distance_sensor`, `force_sensor`, `hub`, `motor`, `motor_pair`, `orientation`, and `runloop`) as direct imports in your environment. Using a virtual environment prevents conflicts with other Python projects and keeps your global Python installation clean.

## Documentation

- [Official GitHub Docs](https://github.com/LEGO/spike-prime-docs)
- [API Reference](https://lego.github.io/spike-prime-docs)
- [Spike 3 Python Docs (Unofficial)](https://tuftsceeo.github.io/SPIKEPythonDocs/SPIKE3.html)

## Running Code on SPIKE

To use MicroPython APIs with auto-complete, place all MicroPython imports inside your `main()` function.

```python
from spikeble import Spike

def main():
    from hub import port
    import motor, time

    # Start motor
    motor.run(port.A, 1000)

if __name__ == "__main__":
    Spike.run(main())
```
