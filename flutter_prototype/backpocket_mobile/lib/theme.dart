import 'dart:ui';
import 'dart:math';
import 'package:flutter/material.dart';

class AppColors {
  static const Color cream = Color(0xFFFAF7F2);
  static const Color terracotta = Color(0xFFC87941);
  static const Color sage = Color(0xFF8FAE8B);
  static const Color brown = Color(0xFF1A1613);

  static const Color bgDark = Color(0xFF0D0A07);
  static const Color surface = Color(0xFF1A1208);
  static const Color card = Color(0xFF211708);
  static const Color border = Color(0x22FFFFFF);
  static const Color amber = Color(0xFFFBBF24);
  static const Color orange = Color(0xFFF97316);
  static const Color red = Color(0xFFEF4444);
  static const Color green = Color(0xFF22C55E);
  static const Color textDim = Color(0x99FFFFFF);
  static const Color textMuted = Color(0x44FFFFFF);
}

class AppTheme {
  static ThemeData get darkTheme => ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.bgDark,
    colorScheme: const ColorScheme.dark(
      primary: AppColors.amber,
      secondary: AppColors.orange,
      surface: AppColors.surface,
      onPrimary: AppColors.brown,
      onSecondary: Colors.white,
      onSurface: AppColors.cream,
    ),
    useMaterial3: true,
  );
}

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
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: Colors.white.withAlpha((opacity * 255).round()),
        borderRadius: borderRadius ?? BorderRadius.circular(16),
        border: Border.all(
          color: (borderColor ?? Colors.white).withAlpha(77),
          width: borderWidth,
        ),
      ),
      child: ClipRRect(
        borderRadius: borderRadius ?? BorderRadius.circular(16),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Padding(padding: padding ?? EdgeInsets.zero, child: child),
        ),
      ),
    );
  }
}

class GlowBorder extends StatelessWidget {
  final Widget child;
  final Color glowColor;
  final double glowRadius;
  final bool isActive;

  const GlowBorder({
    super.key,
    required this.child,
    this.glowColor = AppColors.amber,
    this.glowRadius = 8.0,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: isActive
          ? BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: glowColor.withAlpha(128),
                  blurRadius: glowRadius,
                  spreadRadius: 2,
                ),
              ],
            )
          : null,
      child: child,
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
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 13,
            ),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(color: color.withAlpha(179), fontSize: 11),
          ),
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
    )..repeat(reverse: true);
    _animation = Tween<double>(
      begin: 1.0,
      end: 1.08,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
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
      builder: (context, child) {
        return Transform.scale(scale: _animation.value, child: child);
      },
      child: Container(
        width: widget.size,
        height: widget.size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: AppColors.amber.withAlpha(128), width: 2),
          boxShadow: [
            BoxShadow(
              color: AppColors.amber.withAlpha(51),
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
                  child: const Icon(
                    Icons.person,
                    color: AppColors.amber,
                    size: 40,
                  ),
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
  final List<Offset> _points = [];

  _GrainPainter({required this.opacity}) {
    final random = DateTime.now().millisecondsSinceEpoch;
    for (int i = 0; i < 2000; i++) {
      _points.add(
        Offset(
          (random * (i + 1) * 17 % 1000) / 1000,
          (random * (i + 1) * 23 % 1000) / 1000,
        ),
      );
    }
  }

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
