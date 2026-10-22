Source: [https://www.mobilebuildmcp.com/docs/device-signing](<https://www.mobilebuildmcp.com/docs/device-signing>)

<a id="device-code-signing"></a>

# Device Code Signing

Getting device tools to install and launch on real hardware.

One-time setup required in Xcode

MobileBuildMCP cannot configure code signing automatically. You need to complete this once in Xcode, after which the device workflow tools work unattended.

<a id="steps"></a>

## Steps[#](#steps)

1. Open your project in Xcode.
2. Select your project target.
3. Open the **Signing & Capabilities** tab.
4. Enable **Automatically manage signing** and select your development team.
5. Ensure a valid provisioning profile is selected.

<a id="what-mobilebuildmcp-can-and-cannot-do"></a>

## What MobileBuildMCP can and cannot do[#](#what-mobilebuildmcp-can-and-cannot-do)

|  | MobileBuildMCP |
| --- | --- |
| Build, install, launch, test on paired devices once signing is configured | ✓ |
| Capture runtime logs and pids from device apps | ✓ |
| Configure code signing automatically | ✗ |
| Create or manage provisioning profiles | ✗ |
| Enroll a new development team | ✗ |

<a id="verifying"></a>

## Verifying[#](#verifying)

After configuring signing, plug in your device, trust the computer, and confirm it's visible to the CLI:

shell

```
mobilebuildmcp device list
```

If the device shows as `unreachable`, re-pair it over USB first in **Window → Devices and Simulators** inside Xcode.

<a id="wi-fi-devices"></a>

## Wi-Fi devices[#](#wi-fi-devices)

MobileBuildMCP detects devices paired over Wi-Fi as well as USB. Device discovery uses Apple's `devicectl` under the hood, so Wi-Fi pairing from Xcode carries over directly.

<a id="related"></a>

## Related[#](#related)

- [Troubleshooting](https://www.mobilebuildmcp.com/docs/troubleshooting)
- [Tools Reference](https://www.mobilebuildmcp.com/docs/tools) (filter for the `device` workflow)

[← Previous

Xcode IDE Bridge](https://www.mobilebuildmcp.com/docs/xcode-ide)[Next →

Agent Skills](https://www.mobilebuildmcp.com/docs/skills)
