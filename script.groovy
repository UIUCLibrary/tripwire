#!groovy
// println("hello world!")
def userInput = [
    axes: [
        [
            name: 'PYTHON_VERSION',
            values: ['3.11', '3.12','3.13']
        ],
        [
            name: 'OS',
            values: ['linux','macos','windows']
        ],
        [
            name: 'ARCHITECTURE',
            values: ['x86_64', 'arm64']
        ],
        [
            name: 'PACKAGE_TYPE',
            values: ['wheel', 'sdist'],
        ]
    ],
    excludes: [
        [
            [
                name: 'OS',
                values: 'windows'
            ],
            [
                name: 'ARCHITECTURE',
                values: ['arm64'],
            ]
        ]
    ]
]

// Function to generate all permutations, with support for exclusion lists
def generatePermutations(List<Map> inputMaps, List<List<Map>> exclusions = []) {
    // Generate all possible combinations from the input maps
    def combinations = getCombinations(inputMaps)

    // Filter combinations based on exclusions
    def filteredCombinations = combinations.findAll { combination ->
        // Check each exclusion list to see if any of the combinations should be excluded
        !exclusions.any { exclusionList ->
            exclusionList.every { exclusion ->
                def mapInCombination = combination.find { it.name == exclusion.name }

                // If exclusion value is a list, check if the value is in the exclusion list
                if (exclusion.values instanceof List) {
                    return exclusion.values.contains(mapInCombination?.value)
                }
                // If exclusion value is a single string, check if the value matches the exclusion
                else {
                    return mapInCombination?.value == exclusion.values
                }
            }
        }
    }

    return filteredCombinations
}

// Helper function to generate all combinations of values
def getCombinations(List<Map> maps) {
    // Start with a list containing an empty map
    def result = [[]]

    maps.each { map ->
        def tempResult = []
        map.values.each { value ->
            result.each { combination ->
                tempResult.add(combination + [name: map.name, value: value])
            }
        }
        result = tempResult
    }

    return result
}

def permutations = generatePermutations(userInput.axes, userInput.excludes).collect(row -> row.collectEntries{ element -> [element.name, element.value]})

