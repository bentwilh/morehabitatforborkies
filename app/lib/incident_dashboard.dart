import 'dart:async';
import 'dart:convert';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:gap/gap.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:lottie/lottie.dart' as l;
import 'package:tumai/global.dart';
import 'package:tumai/repository.dart';

import 'incident.dart';

typedef CloseCallback = void Function();
class IncidentDashboard extends StatefulWidget {

  final Marker currentMarker;
  final CloseCallback callback;

  const IncidentDashboard({super.key, required this.currentMarker, required this.callback});

  @override
  State<IncidentDashboard> createState() => _IncidentDashboardState();
}

class _IncidentDashboardState extends State<IncidentDashboard> {

  bool loading = false;
  String? imageNow;
  List<String>? otherImages;

  @override
  void initState() {
    super.initState();
    fetchData();
  }

  Future<void> fetchData() async {
    setState(() {
      loading = true;
    });
    print("Now starting the request");
    Map<String, String> map = await ForestDataRepository().getForestChangeData(
        ForestRequestDto(
            lat: widget.currentMarker.position.latitude,
            lon: widget.currentMarker.position.longitude,
            startYear: 2023,
            startMonth: 8,
            endYear: 2023,
            endMonth: 12)
    );
    print("Now ending the request");
    imageNow = map.entries.last.value;
    otherImages = map.entries.toList().map((e) => e.value).toList();
    setState(() {
      loading = false;
    });
  }



  @override
  Widget build(BuildContext context) {
    Widget child = Container();

    if (loading) {
      child = LoadingIndicator();
    }
    else if (imageNow != null) {
      child = Column(
        children: [
          Flexible(flex: 1, child: CloseButtonRow(widget.callback)),
          Flexible(flex: 6, child: ImageSection(otherImages: otherImages!, imageNow: imageNow!,)), // Image
          Flexible(flex: 4, child: IncidentSection()), // History
        ],
      );} else {
      child = Container();
    }
    return Padding(
      padding: EdgeInsets.only(
          top: 48,
          right: 36,
          left: MediaQuery.of(context).size.width / 3,
          bottom: 48),
      child: SizedBox.expand(
          child: Card(
              elevation: 16,
              child: child)),
    );
  }
}

class CloseButtonRow extends StatelessWidget {

  final CloseCallback callback;

  CloseButtonRow(this.callback);

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topRight,
      child: GestureDetector(
        child: const Padding(
          padding: EdgeInsets.only(top: 18.0, right: 18.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text("Close"),
              Gap(4),
              Icon(Icons.close),
            ],
          ),
        ),
        onTap: () {
          callback.call();
        },
      ),
    );
  }
}

class ImageSection extends StatelessWidget {

  final List<String> otherImages;
  final String imageNow;

  ImageSection({required this.otherImages, required this.imageNow});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: [
        ImageRotationWidget(images: otherImages),
        ImageWidget(base64encodedImage: imageNow),
      ],
    );
  }
}

class ImageRotationWidget extends StatefulWidget {
  final List<String> images;

  const ImageRotationWidget({super.key, required this.images});

  @override
  State<ImageRotationWidget> createState() => _ImageRotationWidgetState();
}

class _ImageRotationWidgetState extends State<ImageRotationWidget> {

  int rotator = 0;

  @override
  void initState() {
    super.initState();
    Timer.periodic(const Duration(milliseconds: 4321), (timer) {
      setState(() {
        rotator++;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return ImageWidget(base64encodedImage: widget.images[rotator % (widget.images.length-1)]);
  }
}

class ImageWidget extends StatelessWidget {
  final String base64encodedImage;

  const ImageWidget({super.key, required this.base64encodedImage});
  @override
  Widget build(BuildContext context) {
    return Image.memory(base64Decode(base64encodedImage));
  }

}

class IncidentSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        IncidentTitleRow(),
        const StatisticsRow(values: {'-10%':'Wach', '69420':'Merge Conflicts', '100%': 'Spaß'}),
        const Expanded(child: IncidentList())
      ],
    );
  }
}

class IncidentTitleRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [const IncidentTitle(title: '1.123123, 32.123432'),
        IncidentActionButtonRow()],
    );
  }

}

class IncidentTitle extends StatelessWidget {

  final String title;

  const IncidentTitle({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topLeft,
      child: Padding(
        padding: const EdgeInsets.only(left: 16.0),
        child: Text(title,
        style: const TextStyle(
          color: Colors.black,
          fontSize: 40,
          fontWeight: FontWeight.w700
        ),),
      ),
    );
  }
}

class StatisticsRow extends StatelessWidget {
  final Map<String, String> values;

  const StatisticsRow({super.key, required this.values});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: values.entries
          .map((e) => StatisticsText(value: e.key, subtext: e.value))
          .toList(),
    );
  }
}

class StatisticsText extends StatelessWidget {
  final String value;
  final String subtext;

  const StatisticsText({super.key, required this.value, required this.subtext});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
              fontSize: 32, fontWeight: FontWeight.w400, color: Colors.blue),
        ),
        const Gap(4),
        Text(
          subtext,
          style: const TextStyle(
              fontSize: 16, fontWeight: FontWeight.w200, color: Colors.black54),
        )
      ],
    );
  }
}

class IncidentActionButtonRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [ResolveIncidentButton(), const Gap(12), AddPersonButton()],
    );
  }
}

class IncidentList extends StatelessWidget {
  const IncidentList({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(valueListenable: incidents,
    builder: (BuildContext context, List<Incident> value, Widget? child) {
      print("Building...");
      return ListView.separated(itemBuilder: (context, index) {
        return IncidentCard(title: value[index].title, timestamp: value[index].timestamp.toIso8601String().split('T')[0], report: value[index].content);
      }, separatorBuilder: (context, index) => Container(height: 0), itemCount: value.length);
    });
  }
}

class ResolveIncidentButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return TextButton(
        onPressed: () async {
          await ForestDataRepository().callNumber();
        },
        child: const Row(
          children: [
            Icon(Icons.done_all_outlined),
            Gap(4),
            Text('Resolve Incident', style: TextStyle(
              fontSize: 32
            ),),
          ],
        ));
  }
}

class AddPersonButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return TextButton(
        onPressed: () async {

        },
        child: const Row(
          children: [
            Icon(Icons.person_add_alt),
            Gap(4),
            Text('Add Person', style: TextStyle(
                fontSize: 32
            )),
          ],
        ));
  }
}

class IncidentCard extends StatelessWidget {
  final String title;
  final String timestamp;
  final String report;

  const IncidentCard(
      {super.key,
      required this.title,
      required this.timestamp,
      required this.report});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 120,
      width: 350,
      child: Material(
        child: Card(
          color: Colors.white,
          shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(16))),
          elevation: 6,
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.all(4.0),
                child: Align(
                  alignment: Alignment.topLeft,
                  child: Text(
                    title,
                    style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w400,
                        color: Colors.black87),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(4.0),
                child: Align(
                  alignment: Alignment.topRight,
                  child: Text(
                    timestamp,
                    style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w200,
                        color: Colors.black54),
                  ),
                ),
              ),
              Align(
                alignment: Alignment.topLeft,
                child: Padding(
                  padding: const EdgeInsets.only(top: 32.0),
                  child: Text(
                    report,
                    style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w200,
                        color: Colors.black54),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


class LoadingIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          l.Lottie.network(
              'https://lottie.host/c63d9754-1947-422b-997e-e1fc1875ea48/7MxCiNgUaP.json',
              width: 200,
              height: 200),
          const Gap(16),
          const Text('Loading...'),
        ],
      ),
    );
  }
}