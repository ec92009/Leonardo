import SwiftUI

@main
struct LeonardoCompanionApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var outputFolder = "./from_leonardo"
    @State private var numberOfDays = "2"
    @State private var generationsToSkip = "0"
    @State private var outputText = ""
    
    @State private var isExecuting = false
    @State private var stopExecution = false
    
    var body: some View {
        VStack(spacing: 10) {
            HStack {
                Text("Output Folder:")
                TextField("", text: $outputFolder)
                Button(action: browseDirectory) {
                    Text("...")
                }
            }
            
            HStack {
                Text("Number of Days:")
                TextField("", text: $numberOfDays)
                    .frame(width: 60)
                    .textFieldStyle(.roundedBorder)
            }
            
            HStack {
                Text("Generations to Skip:")
                TextField("", text: $generationsToSkip)
                    .frame(width: 60)
                    .textFieldStyle(.roundedBorder)
            }
            
            Button(action: {
                startExtraction()
            }) {
                Text("Start Extraction to folder \(outputFolder), for the last \(numberOfDays) days, skipping the newest \(generationsToSkip) generations")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .disabled(isExecuting)
            
            Button(action: stopExtraction) {
                Text("Stop Execution")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.red)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .disabled(!isExecuting || stopExecution)
            
            Button(action: clearOutputText) {
                Text("Clear Output")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.gray)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            
            ScrollView {
                Text(outputText)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .padding()
                    .border(Color.gray, width: 1)
            }
        }
        .padding()
        .frame(width: 400, height: 500)
        .onAppear {
            updateButtonLabel()
        }
    }
    
    func browseDirectory() {
        let dialog = NSOpenPanel()
        dialog.canChooseFiles = false
        dialog.canChooseDirectories = true
        dialog.allowsMultipleSelection = false
        
        if dialog.runModal() == .OK {
            if let url = dialog.urls.first {
                outputFolder = url.path
            }
        }
    }
    
    func startExtraction() {
        isExecuting = true
        stopExecution = false
        updateButtonLabel()
        
        let command = "/Users/ecohen/Documents/Developer/AI/Leonardo/venv/bin/python -V"
//        let command = "/Users/ecohen/Documents/Developer/AI/Leonardo/venv/bin/python -m /Users/ecohen/Documents/Developer/AI/Leonardo/2extraction -l \(outputFolder) -d \(numberOfDays) -s \(generationsToSkip)"
        let task = Process()
        task.launchPath = "/bin/bash"
        task.arguments = ["-c", command]
        
        let outputPipe = Pipe()
        task.standardOutput = outputPipe
        
        let outputHandle = outputPipe.fileHandleForReading
        outputHandle.readabilityHandler = { handle in
            if let line = String(data: handle.availableData, encoding: .utf8) {
                DispatchQueue.main.async {
                    outputText += line
                }
            }
        }
        
        task.terminationHandler = { process in
            DispatchQueue.main.async {
                isExecuting = false
                stopExecution = false
                updateButtonLabel()
            }
        }
        
        do {
            try task.run()
        } catch {
            isExecuting = false
            stopExecution = false
            updateButtonLabel()
            print("Error executing command: \(error)")
        }
    }
    
    func stopExtraction() {
        stopExecution = true
        updateButtonLabel()
    }
    
    func clearOutputText() {
        outputText = ""
    }
    
    func updateButtonLabel() {
        let buttonLabel = "Start Extraction to folder \(outputFolder), for the last \(numberOfDays) days, skipping the newest \(generationsToSkip) generations"
        DispatchQueue.main.async {
            isExecuting ? () : (stopExecution ? () : ())
            stopExecution ? () : ()
        }
    }
}
