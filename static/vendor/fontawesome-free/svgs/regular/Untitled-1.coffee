<!DOCTYPE html>
<html>
<head>
    <title>CBT Error Corrector Flow</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="mermaid">
        graph TD
            A[User Login] --> B{Authentication}
            B -->|Failed| A
            B -->|Success| C[Dashboard]
            
            C --> D[Upload Files]
            D --> E{Check Batch IDs}
            E -->|Mismatch| D
            E -->|Match| F[Process Files]
            
            F --> G[Process Customer XML]
            F --> H[Process Error XML]
            
            G --> I[Store Customer Data]
            H --> J[Store Error Details]
            
            I --> K[Update Dashboard]
            J --> K
            
            K --> L{Error Status}
            L --> M[Pending Errors]
            L --> N[Resolved Errors]
            L --> O[Recent Errors]
            
            M --> P[View Details]
            N --> P
            O --> P
            
            P --> Q{Actions}
            Q --> R[Generate Report]
            Q --> S[Update Status]
            Q --> T[Add Notes]
            
            S --> U{Status Types}
            U --> V[Mark as Resolved]
            U --> W[Mark as Pending]
            U --> X[Mark as Ignored]
            
            V --> K
            W --> K
            X --> K
            
            subgraph Documentation
                Y[View Documentation]
                Y --> Z[Field Rules]
                Y --> AA[Format Guidelines]
                Y --> AB[Regex Patterns]
            end
    </div>
    <script>
        mermaid.initialize({ startOnLoad: true });
    </script>
</body>
</html>