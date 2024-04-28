import 'package:flutter/cupertino.dart';
import 'package:tumai/IncidentEntry.dart';
import 'package:tumai/incident.dart';

ValueNotifier<List<Incident>> incidents = ValueNotifier(<Incident>[]);
ValueNotifier<List<IncidentEntry>> incidentEntries = ValueNotifier(<IncidentEntry>[]);
bool weAreDone = false;