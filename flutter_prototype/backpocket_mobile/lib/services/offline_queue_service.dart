import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'server_url.dart';

bool _hasInternetConnection(List<ConnectivityResult> results) {
  return !results.contains(ConnectivityResult.none);
}

String? _expectedSyncIdentifier(String intent) {
  switch (intent) {
    case 'construction.lead.create':
      return 'lead_id';
    case 'construction.quote.create':
      return 'quote_id';
    case 'construction.payment.record':
      return 'payment_id';
    default:
      return null;
  }
}

bool _responseIncludesIdentifier(
  Map<String, dynamic> responseBody,
  String identifier,
) {
  if (responseBody[identifier] != null) {
    return true;
  }

  final data = responseBody['data'];
  return data is Map && data[identifier] != null;
}

class OfflineQueueService {
  static final OfflineQueueService _instance = OfflineQueueService._internal();
  factory OfflineQueueService() => _instance;
  OfflineQueueService._internal();

  Database? _db;
  int _memoryId = 1;
  final List<Map<String, dynamic>> _memoryVoiceCommands = [];
  final List<Map<String, dynamic>> _memoryOfflineActions = [];
  final Map<String, Map<String, dynamic>> _memoryModelRegistry = {};

  Future<Database> get database async {
    if (kIsWeb) {
      throw UnsupportedError('sqflite offline queue is not available on web.');
    }
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'offline_queue.db');

    return await openDatabase(
      path,
      version: 3,
      onCreate: (db, version) async {
        await _createSchema(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute('''
            CREATE TABLE offline_actions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              client_action_id TEXT NOT NULL UNIQUE,
              intent TEXT NOT NULL,
              transcript TEXT NOT NULL,
              screen_context TEXT NOT NULL,
              payload TEXT,
              response_json TEXT,
              sync_required INTEGER NOT NULL DEFAULT 1,
              sync_status TEXT NOT NULL DEFAULT 'pending',
              error_message TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              synced_at TIMESTAMP
            )
          ''');
          await db.execute('''
            CREATE TABLE model_registry (
              model_id TEXT PRIMARY KEY,
              status TEXT NOT NULL,
              local_path TEXT,
              message TEXT,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
          ''');
        }
        if (oldVersion < 3) {
          await db.execute(
            "ALTER TABLE voice_commands ADD COLUMN client_action_id TEXT",
          );
          await db.execute(
            "ALTER TABLE voice_commands ADD COLUMN sync_status TEXT DEFAULT 'pending'",
          );
        }
      },
    );
  }

  Future<void> _createSchema(Database db) async {
    await db.execute('''
      CREATE TABLE voice_commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transcript TEXT NOT NULL,
        screen_context TEXT NOT NULL,
        session_id TEXT,
        metadata TEXT,
        audio_path TEXT,
        client_action_id TEXT,
        sync_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    ''');
    await db.execute('''
      CREATE TABLE offline_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_action_id TEXT NOT NULL UNIQUE,
        intent TEXT NOT NULL,
        transcript TEXT NOT NULL,
        screen_context TEXT NOT NULL,
        payload TEXT,
        response_json TEXT,
        sync_required INTEGER NOT NULL DEFAULT 1,
        sync_status TEXT NOT NULL DEFAULT 'pending',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        synced_at TIMESTAMP
      )
    ''');
    await db.execute('''
      CREATE TABLE model_registry (
        model_id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        local_path TEXT,
        message TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    ''');
  }

  Future<int> queueVoiceCommand({
    required String transcript,
    required String screenContext,
    String? sessionId,
    Map<String, dynamic>? metadata,
    String? audioPath,
    String? clientActionId,
  }) async {
    if (kIsWeb) {
      final id = _memoryId++;
      _memoryVoiceCommands.add({
        'id': id,
        'transcript': transcript,
        'screen_context': screenContext,
        'session_id': sessionId,
        'metadata': metadata != null ? jsonEncode(metadata) : null,
        'audio_path': audioPath,
        'client_action_id': clientActionId,
        'sync_status': 'pending',
        'created_at': DateTime.now().toIso8601String(),
      });
      return id;
    }

    final db = await database;
    return await db.insert('voice_commands', {
      'transcript': transcript,
      'screen_context': screenContext,
      'session_id': sessionId,
      'metadata': metadata != null ? jsonEncode(metadata) : null,
      'audio_path': audioPath,
      'client_action_id': clientActionId,
    });
  }

  Future<List<Map<String, dynamic>>> getQueuedCommands() async {
    if (kIsWeb) {
      return List<Map<String, dynamic>>.from(_memoryVoiceCommands);
    }

    final db = await database;
    return await db.query('voice_commands', orderBy: 'created_at ASC');
  }

  Future<void> removeCommand(int id) async {
    if (kIsWeb) {
      _memoryVoiceCommands.removeWhere((row) => row['id'] == id);
      return;
    }

    final db = await database;
    await db.delete('voice_commands', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> recordOfflineAction({
    required String clientActionId,
    required String intent,
    required String transcript,
    required String screenContext,
    Map<String, dynamic>? payload,
    Map<String, dynamic>? responseJson,
    bool syncRequired = true,
  }) async {
    if (kIsWeb) {
      _memoryOfflineActions.removeWhere(
        (row) => row['client_action_id'] == clientActionId,
      );
      _memoryOfflineActions.add({
        'id': _memoryId++,
        'client_action_id': clientActionId,
        'intent': intent,
        'transcript': transcript,
        'screen_context': screenContext,
        'payload': payload != null ? jsonEncode(payload) : null,
        'response_json': responseJson != null ? jsonEncode(responseJson) : null,
        'sync_required': syncRequired ? 1 : 0,
        'sync_status': syncRequired ? 'pending' : 'local_only',
        'error_message': null,
        'created_at': DateTime.now().toIso8601String(),
        'synced_at': null,
      });
      return;
    }

    final db = await database;
    await db.insert(
      'offline_actions',
      {
        'client_action_id': clientActionId,
        'intent': intent,
        'transcript': transcript,
        'screen_context': screenContext,
        'payload': payload != null ? jsonEncode(payload) : null,
        'response_json': responseJson != null ? jsonEncode(responseJson) : null,
        'sync_required': syncRequired ? 1 : 0,
        'sync_status': syncRequired ? 'pending' : 'local_only',
        'error_message': null,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getPendingOfflineActions() async {
    if (kIsWeb) {
      return _memoryOfflineActions
          .where(
            (row) =>
                row['sync_status'] == 'pending' && row['sync_required'] == 1,
          )
          .map((row) => Map<String, dynamic>.from(row))
          .toList();
    }

    final db = await database;
    return db.query(
      'offline_actions',
      where: 'sync_status = ? AND sync_required = 1',
      whereArgs: ['pending'],
      orderBy: 'created_at ASC',
    );
  }

  Future<int> getPendingOfflineActionCount() async {
    if (kIsWeb) {
      return _memoryOfflineActions
          .where(
            (row) =>
                row['sync_status'] == 'pending' && row['sync_required'] == 1,
          )
          .length;
    }

    final db = await database;
    final result = await db.rawQuery(
      "SELECT COUNT(*) AS count FROM offline_actions WHERE sync_status = 'pending' AND sync_required = 1",
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  Future<void> markOfflineActionSynced(
    int id, {
    Map<String, dynamic>? serverResponse,
  }) async {
    if (kIsWeb) {
      final index = _memoryOfflineActions.indexWhere((row) => row['id'] == id);
      if (index >= 0) {
        _memoryOfflineActions[index] = {
          ..._memoryOfflineActions[index],
          'sync_status': 'synced',
          'response_json':
              serverResponse != null ? jsonEncode(serverResponse) : null,
          'error_message': null,
          'synced_at': DateTime.now().toIso8601String(),
        };
      }
      return;
    }

    final db = await database;
    await db.update(
      'offline_actions',
      {
        'sync_status': 'synced',
        'response_json':
            serverResponse != null ? jsonEncode(serverResponse) : null,
        'error_message': null,
        'synced_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> markOfflineActionError(int id, String message) async {
    if (kIsWeb) {
      final index = _memoryOfflineActions.indexWhere((row) => row['id'] == id);
      if (index >= 0) {
        _memoryOfflineActions[index] = {
          ..._memoryOfflineActions[index],
          'error_message': message,
          'sync_status': 'pending',
        };
      }
      return;
    }

    final db = await database;
    await db.update(
      'offline_actions',
      {'error_message': message, 'sync_status': 'pending'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> upsertModelRegistry({
    required String modelId,
    required String status,
    required String localPath,
    required String message,
  }) async {
    if (kIsWeb) {
      _memoryModelRegistry[modelId] = {
        'model_id': modelId,
        'status': status,
        'local_path': localPath,
        'message': message,
        'updated_at': DateTime.now().toIso8601String(),
      };
      return;
    }

    final db = await database;
    await db.insert(
      'model_registry',
      {
        'model_id': modelId,
        'status': status,
        'local_path': localPath,
        'message': message,
        'updated_at': DateTime.now().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<Map<String, dynamic>?> getModelRegistry(String modelId) async {
    if (kIsWeb) {
      final row = _memoryModelRegistry[modelId];
      return row == null ? null : Map<String, dynamic>.from(row);
    }

    final db = await database;
    final rows = await db.query(
      'model_registry',
      where: 'model_id = ?',
      whereArgs: [modelId],
      limit: 1,
    );
    return rows.isEmpty ? null : rows.first;
  }

  Future<bool> hasInternet() async {
    final connectivityResult = await (Connectivity().checkConnectivity());
    return _hasInternetConnection(connectivityResult);
  }

  Stream<bool> connectivityChanges() {
    return Connectivity().onConnectivityChanged
        .map(_hasInternetConnection)
        .distinct();
  }

  Future<Map<String, dynamic>?> syncActionToServer({
    required String baseUrl,
    required String apiKey,
    required Map<String, dynamic> action,
  }) async {
    final intent = action['intent'] as String? ?? '';
    final payload = action['payload'] != null
        ? Map<String, dynamic>.from(jsonDecode(action['payload'] as String))
        : <String, dynamic>{};
    payload['client_action_id'] = action['client_action_id'];

    Uri? uri;
    switch (intent) {
      case 'construction.lead.create':
        uri = Uri.parse('${normalizeServerUrl(baseUrl)}/api/construction/leads');
      case 'construction.quote.create':
        uri = Uri.parse('${normalizeServerUrl(baseUrl)}/api/construction/quotes');
      case 'construction.payment.record':
        uri = Uri.parse('${normalizeServerUrl(baseUrl)}/api/construction/payments');
      default:
        return null;
    }

    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
      },
      body: jsonEncode(payload),
    );

    if (response.statusCode != 200) {
      throw Exception('Sync failed with status ${response.statusCode}');
    }

    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw Exception('Sync failed: invalid server response.');
    }

    final responseBody = Map<String, dynamic>.from(decoded);
    final status = responseBody['status']?.toString().toLowerCase();
    if (status == 'error' || responseBody['error'] != null) {
      final message =
          responseBody['message']?.toString() ??
          responseBody['error']?.toString() ??
          'Sync failed without an error message.';
      throw Exception(message);
    }

    final expectedIdentifier = _expectedSyncIdentifier(intent);
    if (expectedIdentifier != null &&
        !_responseIncludesIdentifier(responseBody, expectedIdentifier)) {
      throw Exception(
        'Sync failed: response missing expected $expectedIdentifier.',
      );
    }

    return responseBody;
  }
}
