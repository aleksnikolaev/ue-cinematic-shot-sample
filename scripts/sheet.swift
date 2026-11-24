import AppKit
// usage: sheet out.png w h cols file1 file2 ...
let out = URL(fileURLWithPath: CommandLine.arguments[1])
let cw = Int(CommandLine.arguments[2])!, chh = Int(CommandLine.arguments[3])!
let cols = Int(CommandLine.arguments[4])!
let files = CommandLine.arguments[5...].map { URL(fileURLWithPath: $0) }
let rows = (files.count + cols - 1) / cols
let W = cw * cols, H = chh * rows
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: W, pixelsHigh: H, bitsPerSample: 8,
    samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
for (i, f) in files.enumerated() {
    guard let img = NSImage(contentsOf: f) else { continue }
    let x = (i % cols) * cw, y = H - ((i / cols) + 1) * chh
    img.draw(in: NSRect(x: x, y: y, width: cw, height: chh))
    let label = NSAttributedString(string: " \(i+1) ", attributes: [
        .font: NSFont.boldSystemFont(ofSize: 22), .foregroundColor: NSColor.yellow,
        .backgroundColor: NSColor.black])
    label.draw(at: NSPoint(x: x + 6, y: y + 6))
}
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: out)
print("\(files.count) кадров -> \(out.lastPathComponent) \(W)x\(H)")
