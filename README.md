# Fly or Drive

An app to help you determine whether you should fly somewhere, or turn it into a road trip.

- prices: flight, rental car, gas, hotels
- time
- scenery

## Steps
1. do all the setup bullshit
- db setup
- url config whatnot
- initial evolutions
2. define API

## TODO
- support random towns
  - lookup once the list of places skyscanner supports
  - geocode origin/destination and fetch closest few airports
  - calculate it for each one... and give avg? idk
    - or actually make it more interactive/impressive idk and have it ask which airport you want
  - add driving time to/from airport
- get rental cars working
  - find some API that isn't god awful (or just ask user for prices)
  - ask how many days planning to use car for, calculate
  - rental car needs gas too!
- depending on how weird the solution space is... could we auto-suggest like fly here and rent car instead of flying to exact?  

- call geocode on each of the airport codes and save each one in db for future reference
- needed to support the haversine lookup
  
## Clean up
- break gateway funcs down: just get the data and return it in py form, that's all
- add service mehtods to support those gateways then
- remove hardcodes: magic numbers, localhost, urls etc