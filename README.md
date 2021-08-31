# Fly or Drive

An app to help you determine whether you should fly somewhere, or turn it into a road trip.

![](media/flyordrive-example.gif)

## Usage
To run the app yourself, you'll need API keys. As of now, you need a key for Google and another for SkyScanner

You can run the server from the django project directory:

```shell
fly-or-drive/flyordrive $ python manage.py runserver
```

And then you can access the API via any client you like, but I've included a basic CLI client:

```shell
fly-or-drive/cli_client $ python main.py

```

### TODO
- fetch rental car prices
- add more airports
- fetch hotel prices
- use latest gas prices instead of hardcoded value
- more accurate flight information
  - skyscanner's API is lacking. it doesn't include flight duration, so we assume for now that all flights are direct, and then just use haversine to calculate the distance and infer the time from there using average cruising speed
