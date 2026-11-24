import AVFoundation
import AppKit

// usage: frames_to_mp4 <frames_dir> <out.mp4> <fps>
let dir = URL(fileURLWithPath: CommandLine.arguments[1])
let out = URL(fileURLWithPath: CommandLine.arguments[2])
let fps = Int32(CommandLine.arguments.count > 3 ? CommandLine.arguments[3] : "30") ?? 30

let files = (try! FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil))
    .filter { $0.pathExtension.lowercased() == "png" }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }
guard !files.isEmpty else { print("нет кадров"); exit(1) }

guard let first = NSImage(contentsOf: files[0]),
      let firstCG = first.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("не читается первый кадр"); exit(1)
}
let w = firstCG.width, h = firstCG.height
try? FileManager.default.removeItem(at: out)

let writer = try! AVAssetWriter(outputURL: out, fileType: .mp4)
let settings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: w,
    AVVideoHeightKey: h,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 12_000_000,
        AVVideoMaxKeyFrameIntervalKey: fps,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel
    ]
]
let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
input.expectsMediaDataInRealTime = false
let attrs: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA),
    kCVPixelBufferWidthKey as String: w,
    kCVPixelBufferHeightKey as String: h
]
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attrs)
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

var frame: Int64 = 0
for f in files {
    guard let img = NSImage(contentsOf: f),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    var pb: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pb)
    guard let buffer = pb else { continue }
    CVPixelBufferLockBaseAddress(buffer, [])
    let ctx = CGContext(data: CVPixelBufferGetBaseAddress(buffer), width: w, height: h,
                        bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
                        space: CGColorSpaceCreateDeviceRGB(),
                        bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
    ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
    CVPixelBufferUnlockBaseAddress(buffer, [])
    while !input.isReadyForMoreMediaData { usleep(2000) }
    adaptor.append(buffer, withPresentationTime: CMTime(value: frame, timescale: fps))
    frame += 1
}
input.markAsFinished()
let sem = DispatchSemaphore(value: 0)
writer.finishWriting { sem.signal() }
sem.wait()
print("кадров \(frame), \(w)x\(h), \(fps) fps -> \(out.path)")
if writer.status != .completed { print("статус: \(writer.status.rawValue) \(String(describing: writer.error))"); exit(1) }
