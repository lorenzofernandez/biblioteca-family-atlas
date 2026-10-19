import Foundation
import PDFKit
import Vision
struct Item: Codable {let file:String;let page:Int;let id:String?}
struct Candidate:Codable {let text:String;let confidence:Float}
struct Line:Codable {let candidates:[Candidate];let box:[Double]}
struct Result:Codable {let file:String;let page:Int;let text:String;let confidence:Float;let lines:[Line];let seconds:Double;let revision:Int;let languageCorrection:Bool;let width:Int;let height:Int}
let args=CommandLine.arguments
let root=URL(fileURLWithPath:args[1]), input=args[2], path=args[3], shard=Int(args[4])!, workers=Int(args[5])!, correction=args[6]=="true", maxWidth=Double(args[7])!
let rows=try JSONDecoder().decode([Item].self,from:Data(contentsOf:URL(fileURLWithPath:input)))
var done=Set<String>()
if let old=try? String(contentsOfFile:path,encoding:.utf8){for line in old.split(separator:"\n"){if let d=line.data(using:.utf8),let r=try? JSONDecoder().decode(Result.self,from:d){done.insert("\(r.file):\(r.page)")}}}else{FileManager.default.createFile(atPath:path,contents:nil)}
let out=FileHandle(forWritingAtPath:path)!;out.seekToEndOfFile()
var filename="", document:PDFDocument?;var total=0;let started=Date()
for (index,row) in rows.enumerated() where index % workers == shard {
 if done.contains("\(row.file):\(row.page)"){continue}
 if filename != row.file {filename=row.file;document=PDFDocument(url:root.appendingPathComponent(row.file))}
 autoreleasepool {
  let t=Date()
  guard let page=document?.page(at:row.page-1) else {print("ERROR missing \(row.file):\(row.page)");return}
  let img=page.thumbnail(of:NSSize(width:maxWidth,height:maxWidth*0.72),for:.mediaBox)
  let req=VNRecognizeTextRequest();req.recognitionLevel = .accurate;req.recognitionLanguages=["it-IT","fr-FR","en-US","de-DE","es-ES","pt-BR"];req.usesLanguageCorrection=correction;req.automaticallyDetectsLanguage=true;req.minimumTextHeight=0.006
  do {
   try VNImageRequestHandler(data:img.tiffRepresentation!).perform([req])
   let obs=req.results ?? []
   let lines=obs.map { o -> Line in let b=o.boundingBox;return Line(candidates:o.topCandidates(3).map{Candidate(text:$0.string,confidence:$0.confidence)},box:[b.origin.x,b.origin.y,b.size.width,b.size.height]) }
   let result=Result(file:row.file,page:row.page,text:lines.compactMap{$0.candidates.first?.text}.joined(separator:"\n"),confidence:obs.isEmpty ? 0:obs.map{$0.topCandidates(1).first?.confidence ?? 0}.reduce(0,+)/Float(obs.count),lines:lines,seconds:Date().timeIntervalSince(t),revision:req.revision,languageCorrection:correction,width:Int(img.size.width),height:Int(img.size.height))
   out.write(try JSONEncoder().encode(result));out.write(Data([10]));total+=1
  }catch{print("ERROR \(row.file):\(row.page) \(error)");fflush(stdout)}
 }
 if total % 50 == 0 {print("shard \(shard): \(total) new pages, \(Int(Date().timeIntervalSince(started)))s");fflush(stdout)}
}
print("DONE shard \(shard): \(total) pages, \(Date().timeIntervalSince(started))s");fflush(stdout)
