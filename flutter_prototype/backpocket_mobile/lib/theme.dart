import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design tokens mirrored 1:1 from `static/index.html` so Flutter and the web
/// dashboard look like the same product.
class AppColors {
  // Brand (matches CSS :root vars)
  static const Color cream = Color(0xFFFAF7F2);
  static const Color terracotta = Color(0xFFC87941);
  static const Color sage = Color(0xFF8FAE8B);
  static const Color brown = Color(0xFF1A1613);

  // Dark-mode surfaces (5am warehouse sunrise gradient)
  static const Color bgStart = Color(0xFF0A0E27);
  static const Color bgMid = Color(0xFF1A1F3A);
  static const Color bgEnd = Color(0xFF2D1B4E);
  static const Color bgDark = bgStart;

  static const Color surface = Color(0xFF1A1208);
  static const Color card = Color(0xFF211708);
  static const Color border = Color(0x22FFFFFF);

  // Status
  static const Color amber = Color(0xFFFBBF24);
  static const Color orange = Color(0xFFF97316);
  static const Color red = Color(0xFFEF4444);
  static const Color green = Color(0xFF22C55E);

  // Twin Persona Colors (One-Man Army System)
  static const Color estimator = Color(0xFF2563EB); // Blue
  static const Color siteManager = Color(0xFF16A34A); // Green
  static const Color admin = Color(0xFFDC2626); // Red

  // Text — opaque warm tones; pass WCAG AA on all app surfaces
  // textDim  ~11.9:1 on bgStart, ~9.2:1 on surface
  // textMuted ~6.6:1 on bgStart, ~5.1:1 on surface (AA for small text)
  static const Color textDim = Color(0xFFD4C4B4);
  static const Color textMuted = Color(0xFF9E8E7E);

  // Tier tag colors — mirror --tag-*-text from CSS
  static const Color tagBlueBg = Color(0xFFE3EDFA);
  static const Color tagBlueFg = Color(0xFF2563EB);
  static const Color tagGreenBg = Color(0xFFE3F5E8);
  static const Color tagGreenFg = Color(0xFF16A34A);
  static const Color tagAmberBg = Color(0xFFFEF3C7);
  static const Color tagAmberFg = Color(0xFFD97706);
  static const Color tagRedBg = Color(0xFFFEE2E2);
  static const Color tagRedFg = Color(0xFFDC2626);
  static const Color tagPurpleBg = Color(0xFFF3E8FF);
  static const Color tagPurpleFg = Color(0xFF7C3AED);

  // AI accent
  static const Color aiBg = Color(0xFFF0F4FF);
  static const Color aiBorder = Color(0xFFC7D6F5);

  static const LinearGradient appBackground = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [bgStart, bgMid, bgEnd],
    stops: [0.0, 0.5, 1.0],
  );
}

class AppTheme {
  static ThemeData get darkTheme {
    final base = ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Colors.transparent,
      useMaterial3: true,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.terracotta,
        secondary: AppColors.sage,
        surface: AppColors.surface,
        onPrimary: AppColors.cream,
        onSecondary: AppColors.brown,
        onSurface: AppColors.cream,
      ),
    );
    return base.copyWith(
      textTheme: GoogleFonts.barlowTextTheme(base.textTheme).apply(
        bodyColor: AppColors.cream,
        displayColor: AppColors.cream,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: Colors.white.withAlpha(20),
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.terracotta,
          foregroundColor: AppColors.cream,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          textStyle: GoogleFonts.barlow(fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white.withAlpha(15),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.terracotta),
        ),
      ),
    );
  }
}

/// Full-screen gradient background matching the HTML `.bg-image` +
/// SVG noise grain overlay. Wrap `MaterialApp`'s home with this.
class AppBackground extends StatelessWidget {
  final Widget child;
  const AppBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(gradient: AppColors.appBackground),
      child: Stack(
        children: [
          const Positioned.fill(child: IgnorePointer(child: GrainOverlay())),
          child,
        ],
      ),
    );
  }
}

/// Frosted-glass panel — mirrors the HTML's `rgba + backdrop-filter: blur`.
class FrostedGlass extends StatelessWidget {
  final Widget child;
  final double blur;
  final double opacity;
  final Color? borderColor;
  final double borderWidth;
  final EdgeInsets? padding;
  final EdgeInsets? margin;
  final BorderRadius? borderRadius;

  const FrostedGlass({
    super.key,
    required this.child,
    this.blur = 12.0,
    this.opacity = 0.1,
    this.borderColor,
    this.borderWidth = 1.0,
    this.padding,
    this.margin,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    final radius = borderRadius ?? BorderRadius.circular(16);
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: Colors.white.withAlpha((opacity * 255).round()),
        borderRadius: radius,
        border: Border.all(
          color: (borderColor ?? Colors.white).withAlpha(77),
          width: borderWidth,
        ),
      ),
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Padding(padding: padding ?? EdgeInsets.zero, child: child),
        ),
      ),
    );
  }
}

class StatsPill extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final IconData icon;

  const StatsPill({
    super.key,
    required this.label,
    required this.value,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 13),
          ),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color.withAlpha(179), fontSize: 11)),
        ],
      ),
    );
  }
}

class BreathingAvatar extends StatefulWidget {
  final String? imageUrl;
  final double size;
  const BreathingAvatar({super.key, this.imageUrl, this.size = 80});

  @override
  State<BreathingAvatar> createState() => _BreathingAvatarState();
}

class _BreathingAvatarState extends State<BreathingAvatar>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    );
    _animation = Tween<double>(begin: 1.0, end: 1.08)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final reduce = MediaQuery.of(context).disableAnimations;
    if (!reduce && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (reduce && _controller.isAnimating) {
      _controller.stop();
      _controller.reset();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) => Transform.scale(scale: _animation.value, child: child),
      child: Container(
        width: widget.size,
        height: widget.size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: AppColors.terracotta.withAlpha(128), width: 2),
          boxShadow: [
            BoxShadow(
              color: AppColors.terracotta.withAlpha(51),
              blurRadius: 20,
              spreadRadius: 5,
            ),
          ],
        ),
        child: ClipOval(
          child: widget.imageUrl != null
              ? Image.network(widget.imageUrl!, fit: BoxFit.cover)
              : Container(
                  color: AppColors.surface,
                  child: const Icon(Icons.person, color: AppColors.terracotta, size: 40),
                ),
        ),
      ),
    );
  }
}

class GrainOverlay extends StatelessWidget {
  final double opacity;
  const GrainOverlay({super.key, this.opacity = 0.03});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(
        painter: _GrainPainter(opacity: opacity),
        size: Size.infinite,
      ),
    );
  }
}

class _GrainPainter extends CustomPainter {
  final double opacity;

  static final List<Offset> _points = _buildPoints();

  static List<Offset> _buildPoints() {
    const seed = 31415926;
    final pts = <Offset>[];
    for (int i = 0; i < 2000; i++) {
      pts.add(Offset(
        (seed * (i + 1) * 17 % 1000) / 1000,
        (seed * (i + 1) * 23 % 1000) / 1000,
      ));
    }
    return pts;
  }

  const _GrainPainter({required this.opacity});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withAlpha((opacity * 255).round())
      ..style = PaintingStyle.fill;
    for (final point in _points) {
      canvas.drawCircle(
        Offset(point.dx * size.width, point.dy * size.height),
        0.5,
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _GrainPainter oldDelegate) => false;
}
