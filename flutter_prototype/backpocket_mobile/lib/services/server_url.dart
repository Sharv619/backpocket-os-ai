String _withDefaultScheme(String rawUrl) {
  final trimmed = rawUrl.trim();
  if (trimmed.isEmpty) return trimmed;
  if (trimmed.contains('://')) return trimmed;
  return 'http://$trimmed';
}

Uri? tryParseServerUrl(String rawUrl) {
  final candidate = _withDefaultScheme(rawUrl);
  if (candidate.isEmpty) return null;
  return Uri.tryParse(candidate);
}

String normalizeServerUrl(String rawUrl) {
  final trimmed = rawUrl.trim();
  if (trimmed.isEmpty) return trimmed;

  final uri = tryParseServerUrl(trimmed);
  if (uri == null || uri.host.isEmpty) return trimmed;

  final normalized = Uri(
    scheme: uri.scheme.isEmpty ? 'http' : uri.scheme,
    host: uri.host,
    port: uri.hasPort ? uri.port : null,
  ).toString();

  return normalized.endsWith('/')
      ? normalized.substring(0, normalized.length - 1)
      : normalized;
}

bool _isLoopbackHost(String host) {
  final lower = host.toLowerCase();
  return lower == '127.0.0.1' || lower == 'localhost' || lower == '::1';
}

bool isLoopbackServerUrl(String rawUrl) {
  final uri = tryParseServerUrl(rawUrl);
  if (uri == null || uri.host.isEmpty) return false;
  return _isLoopbackHost(uri.host);
}

bool isInsecureRemoteServerUrl(String rawUrl) {
  final uri = tryParseServerUrl(rawUrl);
  if (uri == null || uri.host.isEmpty) return false;
  return uri.scheme == 'http' && !_isLoopbackHost(uri.host);
}

bool hasPathInServerUrl(String rawUrl) {
  final uri = tryParseServerUrl(rawUrl);
  if (uri == null) return false;
  final path = uri.path.trim();
  return path.isNotEmpty && path != '/';
}

bool isValidServerUrl(String rawUrl) {
  final uri = tryParseServerUrl(rawUrl);
  return uri != null && uri.host.isNotEmpty;
}
