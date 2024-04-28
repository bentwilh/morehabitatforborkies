import 'package:meta/meta.dart';
import 'dart:convert';

class IncidentEntry {
  final String? incidentId;
  final String location;
  final DateTime timestamp;

  IncidentEntry({
    this.incidentId,
    required this.location,
    required this.timestamp,
  });

  factory IncidentEntry.fromRawJson(String str) => IncidentEntry.fromJson(json.decode(str));

  String toRawJson() => json.encode(toJson());

  factory IncidentEntry.fromJson(Map<String, dynamic> json) => IncidentEntry(
    incidentId: json["incident_id"],
    location: json["location"],
    timestamp: DateTime.now(),
  );

  Map<String, dynamic> toJson() => {
    "incident_id": incidentId,
    "location": location,
    "timestamp": timestamp.toIso8601String(),
  };
}
