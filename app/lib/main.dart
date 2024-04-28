import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_fadein/flutter_fadein.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:tumai/IncidentEntry.dart';
import 'package:tumai/global.dart';
import 'package:tumai/incident_dashboard.dart';
import 'package:tumai/repository.dart';

Marker? currentMarker;

void main() async {
  await ForestDataRepository().fetchIncidents();
  Timer.periodic(const Duration(milliseconds: 5000), (timer) {
    ForestDataRepository().fetchCalls();
  });
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Wood Watcher',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const MapSample(),
    );
  }
}

class MapSample extends StatefulWidget {
  const MapSample({super.key});

  @override
  State<MapSample> createState() => MapSampleState();
}

class MapSampleState extends State<MapSample> {
  final Completer<GoogleMapController> _controller =
      Completer<GoogleMapController>();

  bool showPopup = false;

  static const CameraPosition initialPosition = CameraPosition(
    target: LatLng(-4.186084, -56.063341,),
    zoom: 14.4746,
  );

  @override
  Widget build(BuildContext context) {
    Widget googleMap = GoogleMap(
      mapType: MapType.hybrid,
      initialCameraPosition: initialPosition,
      onMapCreated: (GoogleMapController controller) {
        _controller.complete(controller);
      },
      markers: Set.from(currentMarker == null ? incidentEntries.value.map((e) => Marker(markerId: MarkerId(e.incidentId ?? "fgeuyfgkseuygfjegsf"), position: LatLng(double.parse(e.location.split(', ')[0]), double.parse(e.location.split(', ')[1])))) : [currentMarker, ...incidentEntries.value.map((e) => Marker(markerId: MarkerId(e.incidentId ?? "fsjfkjnfskjnf"), position: LatLng(double.parse(e.location.split(', ')[0]), double.parse(e.location.split(', ')[1]))))]),
      scrollGesturesEnabled: !showPopup,
      onTap: (pointer) async {
        if (showPopup) {
          return;
        }
        setState(() {
          currentMarker =
              Marker(markerId: const MarkerId("0"), position: pointer, flat: false);
        });
        ForestDataRepository().addIncidentEntry(IncidentEntry(location: '${pointer.latitude}, ${pointer.longitude}', timestamp: DateTime.now()));
        await (await _controller.future).animateCamera(
            CameraUpdate.newCameraPosition(
                CameraPosition(target: pointer, zoom: 18)));
        await (await _controller.future).animateCamera(
            CameraUpdate.scrollBy(MediaQuery.of(context).size.width / 3, 0));
        setState(() {
          showPopup = true;
        });
      },
    );

    return Scaffold(
      body: Stack(
        children: [
          googleMap,
          Align(
            alignment: Alignment.topCenter,
            child: Card(
              margin: EdgeInsets.all(8),
              shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.all(Radius.circular(16))),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Image.asset("assets/woodwatcher.png", width: 250,),
                )),
          ),

          if (showPopup)
            FadeIn(
                duration: const Duration(milliseconds: 1000),
                curve: Curves.elasticIn,
                child: IncidentDashboard(callback: () {
                  setState(() {
                    Future.delayed(Duration(milliseconds: 400), () {
                      setState(() {
                        currentMarker = null;
                        showPopup = false;
                      });
                    },);
                  });

                }, currentMarker: currentMarker!,))
        ],
      ),
    );
  }
}
