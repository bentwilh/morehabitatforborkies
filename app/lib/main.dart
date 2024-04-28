import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_fadein/flutter_fadein.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:tumai/forest_dashboard.dart';
import 'package:tumai/incident_dashboard.dart';

Marker? currentMarker;

void main() {
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
    target: LatLng(1.788250, -61.135222),
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
      markers: Set.from(currentMarker == null ? [] : [currentMarker]),
      scrollGesturesEnabled: !showPopup,
      onTap: (pointer) async {
        if (showPopup) {
          return;
        }
        setState(() {
          currentMarker =
              Marker(markerId: const MarkerId("0"), position: pointer, flat: false);
        });
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
