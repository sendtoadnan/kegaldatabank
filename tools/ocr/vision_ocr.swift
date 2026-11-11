// OCR page images with Apple's Vision framework (macOS, offline).
// usage: vision_ocr [--boxes] img1.png [img2.png ...]  -> prints "=== <file>" then text lines
// --boxes prefixes each line with "x0 y0 x1 y1<TAB>" (0-1, origin top-left)
import Foundation
import Vision
import AppKit

let boxes = CommandLine.arguments.contains("--boxes")
for path in CommandLine.arguments.dropFirst() where path != "--boxes" {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("=== \(path)\n[unreadable]"); continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    req.recognitionLanguages = ["en-US"]
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    let obs = (req.results ?? []).sorted {
        // top-to-bottom, then left-to-right
        abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.008 ? $0.boundingBox.midY > $1.boundingBox.midY : $0.boundingBox.minX < $1.boundingBox.minX
    }
    print("=== \(path)")
    for o in obs {
        guard let t = o.topCandidates(1).first?.string else { continue }
        if boxes {
            let b = o.boundingBox
            print(String(format: "%.4f %.4f %.4f %.4f\t", b.minX, 1 - b.maxY, b.maxX, 1 - b.minY) + t)
        } else { print(t) }
    }
}
