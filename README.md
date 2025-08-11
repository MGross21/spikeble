<h1 align="center">
    <img src="https://raw.githubusercontent.com/MGross21/spikeble/main/assets/spikeble_logo.png" alt="spikeble logo" width="300" />
</h1>
<p align="center">
    <sub>(pronounced "spike-able")</sub>
    <br>
    <img src="https://raw.githubusercontent.com/MGross21/spikeble/main/assets/lego_spike.png" alt="Lego Spike"/>
</p>

## Installation

```bash
pip install git+https://github.com/MGross21/spikeble.git
```

> **⚠️ Warning:**  
> It is **highly recommended** to install and use this library within a Python virtual environment. Installing `spikeble` will expose all MicroPython modules (such as `app`, `color`, `color_matrix`, `color_sensor`, `device`, `distance_sensor`, `force_sensor`, `hub`, `motor`, `motor_pair`, `orientation`, and `runloop`) as direct imports in your environment. Using a virtual environment prevents conflicts with other Python projects and keeps your global Python installation clean.
> **⚠️ Warning:**  
> It is **highly recommended** to install and use this library within a Python virtual environment. Installing `spikeble` will expose all MicroPython modules (such as `app`, `color`, `color_matrix`, `color_sensor`, `device`, `distance_sensor`, `force_sensor`, `hub`, `motor`, `motor_pair`, `orientation`, and `runloop`) as direct imports in your environment. Using a virtual environment prevents conflicts with other Python projects and keeps your global Python installation clean.
>
> <details>
> <summary><strong>Making a Python Virtual Environment</strong></summary>
>
> ```bash
> python -m venv .venv
>
> # Activate the virtual environment
> # On Windows:
> venv\Scripts\activate
>
> # On macOS/Linux:
> source venv/bin/activate
> ```
>
> Once activated, you can install `spikeble` and other dependencies.
>
> </details>

## Running Code on SPIKE

To enable auto-complete for MicroPython APIs, place all MicroPython imports inside your `main()` function.  
Use the template below as a starting point for your SPIKE code:

```python
import spikeble

def main():
    from app import sound, bargraph, display, linegraph, music
    import color
    import color_matrix
    import color_sensor
    import device
    import distance_sensor
    import force_sensor
    from hub import port, button, light, light_matrix, motion_sensor, sound
    import motor
    import motor_pair
    import orientation
    import runloop

    ### Insert Your Code Here ###

if __name__ == "__main__":
    spikeble.run(main())
```

## Documentation

<!-- - [GitHub Docs](https://github.com/LEGO/spike-prime-docs) -->
- [Official API Reference](https://spike.legoeducation.com/prime/modal/help/lls-help-python)
<!-- - [Spike 3 Python Docs (Unofficial)](https://tuftsceeo.github.io/SPIKEPythonDocs/SPIKE3.html) -->