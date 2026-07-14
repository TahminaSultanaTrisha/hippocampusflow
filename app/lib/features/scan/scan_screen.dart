// The core Phase 1 screen. Flow:
//   open -> ask for camera permission -> live preview
//   tap shutter -> capture frame -> upload to backend -> go to scan detail
// On Chrome the "camera" is your webcam; on a phone it's the real camera.
// Same code -- that's Flutter's cross-platform promise doing its job.
import 'package:camera/camera.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme.dart';
import 'scan_repository.dart';

class ScanScreen extends ConsumerStatefulWidget {
  const ScanScreen({super.key});
  @override
  ConsumerState<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends ConsumerState<ScanScreen> {
  CameraController? _controller;
  String? _error;
  bool _uploading = false;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() => _error = 'No camera found on this device.');
        return;
      }
      // Prefer the back camera on phones; on a laptop there's usually one.
      final camera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      final controller = CameraController(
        camera,
        ResolutionPreset.medium, // plenty for AI analysis, fast to upload
        enableAudio: false,
      );
      await controller.initialize();
      if (!mounted) return;
      setState(() => _controller = controller);
    } on CameraException catch (e) {
      setState(() => _error = e.code == 'CameraAccessDenied'
          ? 'Camera permission was denied. Allow camera access and try again.'
          : 'Camera error: ${e.description}');
    }
  }

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || _uploading) return;
    setState(() => _uploading = true);
    try {
      final shot = await controller.takePicture();
      final bytes = await shot.readAsBytes();
      final scan = await ref.read(scanRepositoryProvider).upload(bytes);
      if (!mounted) return;
      context.go('/scans/${scan.id}');
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() => _uploading = false);
      if (e.response?.statusCode == 402) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Free scans used up'),
            content: const Text(
                'You\'ve used all your free scans this month. '
                'Premium with unlimited scans is coming soon — thanks for '
                'being an early user!'),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('OK')),
            ],
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Upload failed — is the backend running?')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _uploading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Upload failed — is the backend running?')),
      );
    }
  }

  @override
  void dispose() {
    _controller?.dispose(); // release the camera when leaving the screen
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(backgroundColor: Colors.transparent, title: const Text('Scan')),
      body: _error != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(_error!, textAlign: TextAlign.center),
              ),
            )
          : _controller == null
              ? const Center(child: CircularProgressIndicator(color: scanGlow))
              : Column(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: CameraPreview(_controller!),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(24),
                      child: GestureDetector(
                        onTap: _capture,
                        child: Container(
                          width: 76,
                          height: 76,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: _uploading ? inkRaised : scanGlow,
                            border: Border.all(color: scanGlow, width: 3),
                          ),
                          child: _uploading
                              ? const Padding(
                                  padding: EdgeInsets.all(20),
                                  child: CircularProgressIndicator(
                                      color: scanGlow, strokeWidth: 3),
                                )
                              : const Icon(Icons.camera_alt, color: inkDeep),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }
}
