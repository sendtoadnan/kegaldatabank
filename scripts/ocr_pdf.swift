// OCR a scanned PDF with macOS's built-in Vision text recognition (no install needed).
// Usage: swift scripts/ocr_pdf.swift <in.pdf> <out.txt> [firstPage] [lastPage]
// Writes the recognised lines in reading order, with "<<<page N>>>" before each page,
// so a reader can find the page in the scan. The text is unverified: OCR makes mistakes.
import Foundation
import PDFKit
import Vision

let args = CommandLine.arguments
guard args.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
  FileHandle.standardError.write("usage: swift scripts/ocr_pdf.swift <in.pdf> <out.txt> [first] [last]\n".data(using: .utf8)!)
  exit(1)
}
let first = args.count > 3 ? max(1, Int(args[3]) ?? 1) : 1
let last = args.count > 4 ? min(doc.pageCount, Int(args[4]) ?? doc.pageCount) : doc.pageCount
var out = ""

for n in first...last {
  guard let page = doc.page(at: n - 1) else { continue }
  // Render at about 300 dpi for accurate recognition.
  let box = page.bounds(for: .mediaBox)
  let scale: CGFloat = 300.0 / 72.0
  let size = CGSize(width: box.width * scale, height: box.height * scale)
  let image = page.thumbnail(of: size, for: .mediaBox)
  guard let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }

  let request = VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.recognitionLanguages = ["en-US"]
  request.usesLanguageCorrection = true
  try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
  let lines = (request.results ?? [])
    .compactMap { obs -> (CGRect, String)? in
      guard let s = obs.topCandidates(1).first?.string else { return nil }
      return (obs.boundingBox, s)
    }
    // Top to bottom (Vision's origin is bottom-left), then left to right on the same line.
    .sorted { a, b in abs(a.0.midY - b.0.midY) > 0.006 ? a.0.midY > b.0.midY : a.0.minX < b.0.minX }
  out += "<<<page \(n)>>>\n" + lines.map { $0.1 }.joined(separator: "\n") + "\n"
  FileHandle.standardError.write("page \(n): \(lines.count) lines\n".data(using: .utf8)!)
}
try! out.write(toFile: args[2], atomically: true, encoding: .utf8)
