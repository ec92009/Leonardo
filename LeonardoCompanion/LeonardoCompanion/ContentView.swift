import SwiftUI

struct ContentView: View {
    @State private var downloadFolder: String = ""
    @State private var apiKey: String = ""
    @State private var days: Int = 7
    @State private var skip: Int = 0
    @State private var includeOriginals: Bool = false
    @State private var includeVariants: Bool = false
    @State private var upscale: Bool = false
    @State private var outputText: String = ""

    var body: some View {
        VStack {
            // UI elements for input parameters
            TextField("Download Folder", text: $downloadFolder)
            TextField("API Key", text: $apiKey)
            Stepper("Days: \(days)", value: $days, in: 1...30)
            Stepper("Skip: \(skip)", value: $skip, in: 0...100)
            Toggle("Include Originals", isOn: $includeOriginals)
            Toggle("Include Variants", isOn: $includeVariants)
            Toggle("Upscale", isOn: $upscale)

            // Start and Stop buttons
            HStack {
                Button("Start") {
                    startScript()
                }
                Button("Stop") {
                    // Logic to stop the script
                }
            }

            // Text view for script output
            Text(outputText)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
        .padding()
    }

    
    private func startScript() {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        
        // Construct the command line arguments
        let scriptURL = Bundle.main.url(forResource: "2extraction", withExtension: "py")!
        var arguments = [String]()
        arguments.append(scriptURL.path)
        arguments.append("--downloadFolder")
        arguments.append(downloadFolder)
        arguments.append("--apiKey")
        arguments.append(apiKey)
        arguments.append("--days")
        arguments.append(String(days))
        // ... add other parameters

        process.arguments = arguments

        let outputPipe = Pipe()
        process.standardOutput = outputPipe
        let errorPipe = Pipe()
        process.standardError = errorPipe

        do {
            try process.run()
            let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
            let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()

            if let output = String(data: outputData, encoding: .utf8) {
                outputText = output
            }
            if let error = String(data: errorData, encoding: .utf8) {
                outputText += "\nError: \(error)"
            }
        } catch {
            outputText = "Error running script: \(error.localizedDescription)"
        }
    }

}



struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
