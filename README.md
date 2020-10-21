# m5-pump-driver

M5Stack MicroPython pump driver

# Setup instructions:

1. Flash lv_micropython-LV_COLOR_DEPTH_16-DLV_COLOR_16_SWAP-roboto12-v1.11-877-gbf7699eee.bin (instructions here).
2. Clone https://sci-bots/m5-pump-driver
3. Use VS Code Pymakr extension to upload m5-pump-driver contents to M5Stack.
4. Attach faces kit with encoder face.

# Notes:

If you can't connect to the esp32 board, try the following steps from the Pymakr extension's "Details" tab:

> 1. Check if the serial port of your board is detected by running 'pymakr > Extra > List Serial ports'
> 2. If it is detected, note the serial port manufactures , ie 'Silicon Labs'
> 3. Add the manufacturmanufacturer to the autoconnect_comport_manufacturers names in you project or global config.
> 4. Re-run 'pymakr > Extra > List Serial ports'
> 5. If the board is not detected as the first, you may need to move it to the front of the list.
