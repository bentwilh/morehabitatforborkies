import 'dart:async';
import 'dart:convert';

import 'package:blurrycontainer/blurrycontainer.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:gap/gap.dart';
import 'package:lottie/lottie.dart';
import 'package:tumai/incident_dashboard.dart';
import 'package:tumai/main.dart';
import 'package:tumai/repository.dart';

String contact = '';

enum ForestDashboardState {
  loading,
  error,
  dataLoaded,
}

typedef CloseCallback = void Function();
class ForestDashboard extends StatelessWidget {

  final CloseCallback callback;

  const ForestDashboard({super.key, required this.callback});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
          top: 48,
          right: 36,
          left: MediaQuery.of(context).size.width / 3,
          bottom: 48),
      child: SizedBox.expand(
          child: Card(
              elevation: 16,
              child: IncidentDashboard())),
    );
  }
}

class ForestDashboardWidget extends StatefulWidget {
  final CloseCallback callback;
  const ForestDashboardWidget(this.callback);

  @override
  _ForestDashboardWidgetState createState() => _ForestDashboardWidgetState();
}

class _ForestDashboardWidgetState extends State<ForestDashboardWidget> {
  ForestDashboardState _dashboardState = ForestDashboardState.loading;
  Map<String, String> _forestData = <String, String>{};
  DateTime _selectedDate = DateTime.now();
  int _currentStep = 0;
  @override
  void initState() {
    super.initState();
    fetchData();
  }

  Future<void> fetchData() async {
    setState(() {
      _dashboardState = ForestDashboardState.loading;
    });
    Map<String, String> map = await ForestDataRepository().getForestChangeData(ForestRequestDto(lat: currentMarker!.position.latitude, lon: currentMarker!.position.longitude, startYear: 2023, startMonth: 1, endYear: 2023, endMonth: 12));
    // Simulate fetching data with delay.
    await Future.delayed(Duration(seconds: 2));
    setState(() {
      _forestData = map;
      _dashboardState = ForestDashboardState.dataLoaded;
    });
    Timer.periodic(Duration(milliseconds: 2000), (timer) {
      setState(() {
      _currentStep++;
      });

    });
  }

  @override
  Widget build(BuildContext context) {
    switch (_dashboardState) {
      case ForestDashboardState.loading:
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Lottie.network(
                  'https://lottie.host/c63d9754-1947-422b-997e-e1fc1875ea48/7MxCiNgUaP.json',
                  width: 100,
                  height: 100),
              SizedBox(height: 16),
              Text('Loading...'),
            ],
          ),
        );
      case ForestDashboardState.error:
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Lottie.network(
                  'https://lottie.host/c63d9754-1947-422b-997e-e1fc1875ea48/7MxCiNgUaP.json',
                  width: 100,
                  height: 100),
              SizedBox(height: 16),
              Text('Error loading data'),
            ],
          ),
        );
      case ForestDashboardState.dataLoaded:
        return _buildDataLoadedLayout();
      default:
        return SizedBox.shrink();
    }
  }

  Widget _buildDataLoadedLayout() {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Column(
              children: [
                _forestData.isNotEmpty
                    ? Image.memory(base64Decode(_forestData.entries.elementAt(_currentStep % _forestData.entries.length).value))
                    : const SizedBox.shrink(),
              ],
            ),
          ),
          Expanded(
              flex: 1,
              child: Column(
                children: [
                  GestureDetector(
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        const Text("Close"),
                        const Gap(4),
                        Icon(Icons.close),
                      ],
                    ),
                    onTap: () {
                      widget.callback.call();
                    },
                  ),
                  Icon(Icons.warning_amber, color: Colors.black87, size: 90,),
                  Text("Wood Watcher measured deforestation in the selected area. Please notify the appropriate contact person", style: TextStyle(fontSize: 24, fontWeight: FontWeight.w400), textAlign: TextAlign.center,),
                  Gap(12),
                  CustomDropDownButton(onOptionSelected: (a) {
                    contact = a;
                  }),
                  Gap(8),
                  CallToActionCallActionButton(),
                ],
              )),
        ],
      ),
    );
  }

  Widget _buildKPIWidget(String title, num value) {
    return KPIWidget(title, value
        // Add other properties needed for SomeKPIWidget
        );
  }
}

class KPIWidget extends StatelessWidget {
  final String title;
  final num value;

  const KPIWidget(this.title, this.value);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [Text('$value'), Text(title)],
    );
  }
}

class CallToActionCallActionButton extends StatefulWidget {
  @override
  State<CallToActionCallActionButton> createState() => _CallToActionCallActionButtonState();
}

class _CallToActionCallActionButtonState extends State<CallToActionCallActionButton> {

  bool loading = false;
  bool success = false;
  bool failure = false;
  String contact = '';

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return Row(
        children: [
          Lottie.network('https://lottie.host/31971e52-d9c8-4e11-85ab-7efa38ed19ea/Re5OZGUhnP.json', height: 50, repeat: true),
          Gap(8),
          Text('We are now calling $contact', style: TextStyle(
            color: Colors.green,
            fontSize: 24
          ),)
        ],
      );
    }
    if (success) {
      Row(
        children: [
          Lottie.network('https://lottie.host/49b315da-0d0e-4d6c-8815-0e2cc9b925bf/uqMYWszPJG.json', height: 50, repeat: false),
          Gap(8),
          Text('$contact was informed about the circumstances', style: TextStyle(
              color: Colors.green,
              fontSize: 24
          ),)
        ],
      );
    }
    if (failure) {
      return Row(
        children: [
          Lottie.network('https://lottie.host/9484d03e-b013-4ce2-b59c-dc6da58aa18a/YHJsCvuZxY.json', height: 50, repeat: false),
          Gap(8),
          Text('We couldn\'t reach $contact, please try again later!', style: TextStyle(
              color: Colors.red,
              fontSize: 24
          ),)
        ],
      );
    }
    return MaterialButton(onPressed: () async {
      setState(() {
        loading = true;
      });
      if (await ForestDataRepository().callNumber()) {
        setState(() {
          success = true;
        });
      } else {
        setState(() {
          failure = true;
        });
      }
    },
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(8))),
    color: Colors.red,
    child: SizedBox(
      width: 160,
      height: 50,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.wifi_calling_3, color: Colors.white, size: 32,),
          Gap(12),
          Text('NOTIFY',  style: TextStyle(
            color: Colors.white,
            fontSize: 24
          ),)
        ],
      ),
    ),);
  }
}

class CustomDropDownButton extends StatefulWidget {
  final Function(String) onOptionSelected;
  const CustomDropDownButton({Key? key, required this.onOptionSelected}) : super(key: key);
  @override
  _CustomDropDownButtonState createState() => _CustomDropDownButtonState();
}
class _CustomDropDownButtonState extends State<CustomDropDownButton> {
  String? _selectedOption;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8.0),
        border: Border.all(
          color: Colors.grey.shade300,
          style: BorderStyle.solid,
          width: 1.0,
        ),
      ),
      child: DropdownButton<String>(
        value: _selectedOption,
        icon: const Icon(Icons.arrow_drop_down),
        iconSize: 24,
        elevation: 16,
        style: const TextStyle(color: Colors.black87),
        underline: Container(
          height: 0, // Hide the default underline
        ),
        onChanged: (String? newValue) {
          setState(() {
            _selectedOption = newValue;
          });
          widget.onOptionSelected(newValue!);
        },
        items: <String>[
          'Emilio (+987654321)',
          'Guilherme (+123456789)',
          'Pedro (+192837465)',
        ].map<DropdownMenuItem<String>>((String value) {
          return DropdownMenuItem<String>(
            value: value,
            child: Text(value),
          );
        }).toList(),
      ),
    );
  }
}
