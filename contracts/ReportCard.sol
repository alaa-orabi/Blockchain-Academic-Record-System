// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReportCard {

    // ═══════════════════════════════════════════════
    //  STATE VARIABLES
    // ═══════════════════════════════════════════════

    address public owner;  // admin wallet
    bool    public paused; // emergency switch

    struct Student {
        string  name;
        uint256 grade;
        bool    isRegistered; // blocks duplicate registration
        bool    hasGrade;     // false until admin assigns a grade
    }

    mapping(address => Student) private students; // main database
    address[] private studentList;                // needed to loop over all students


    
     // ═══════════════════════════════════════════════
    //  EVENTS
    // ═══════════════════════════════════════════════

    event StudentRegistered(address indexed studentAddress, string name);
    event GradeRecorded(address indexed studentAddress, uint256 grade);
    event ContractPaused(address indexed by);
    event ContractResumed(address indexed by);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
   
    // ═══════════════════════════════════════════════
    //  CONSTRUCTOR
    // ═══════════════════════════════════════════════

    constructor() {
        owner  = msg.sender; // deployer becomes the admin
        paused = false;
    }
 
    // ═══════════════════════════════════════════════
    //  MODIFIERS
    // ═══════════════════════════════════════════════

    modifier onlyOwner() {
        require(msg.sender == owner, "Access denied: owner only");
        _; // run the function body after this check
    }

    modifier whenNotPaused() {
        require(!paused, "System is currently paused");
        _;
    }

     // ═══════════════════════════════════════════════
    //  USER FUNCTIONS  (any wallet can call these)
    // ═══════════════════════════════════════════════

    function registerUser(string calldata name) public whenNotPaused {
        require(!students[msg.sender].isRegistered, "Already registered");
        require(bytes(name).length > 0, "Name cannot be empty");

        students[msg.sender].name         = name;
        students[msg.sender].isRegistered = true;
        studentList.push(msg.sender); // save address so we can loop later

        emit StudentRegistered(msg.sender, name);
    }

    function getGrade(address studentAddress)
        public
        view
        returns (string memory name, uint256 grade, bool hasGrade)
    {
        require(students[studentAddress].isRegistered, "No record found for this address");

        Student memory s = students[studentAddress]; // copy to memory (saves gas)
        return (s.name, s.grade, s.hasGrade);
    }


 // ═══════════════════════════════════════════════
    //  ADMIN FUNCTIONS  (owner only)
    // ═══════════════════════════════════════════════

    function addGrade(address studentAddress, uint256 grade)
        public
        onlyOwner
        whenNotPaused
    {
        require(students[studentAddress].isRegistered, "Student is not registered");
        require(grade <= 100, "Grade must be between 0 and 100");

        students[studentAddress].grade    = grade;
        students[studentAddress].hasGrade = true;

        emit GradeRecorded(studentAddress, grade);
    }

    function batchAddGrades(
        address[] memory studentAddresses,
        uint256[]  memory grades
    ) public onlyOwner whenNotPaused {
        require(studentAddresses.length == grades.length, "Address and grade lists must be the same length");

        for (uint256 i = 0; i < studentAddresses.length; i++) { // loop through both arrays
            require(students[studentAddresses[i]].isRegistered, "One or more students are not registered");
            require(grades[i] <= 100, "Grade must be between 0 and 100");

            students[studentAddresses[i]].grade    = grades[i];
            students[studentAddresses[i]].hasGrade = true;

            emit GradeRecorded(studentAddresses[i], grades[i]);
        }
    }

    function pause() public onlyOwner {
        require(!paused, "Already paused");
        paused = true;
        emit ContractPaused(msg.sender);
    }

    function resume() public onlyOwner {
        require(paused, "Not currently paused");
        paused = false;
        emit ContractResumed(msg.sender);
    }

    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "New owner cannot be the zero address");
        emit OwnershipTransferred(owner, newOwner); // emit before changing (logs old owner)
        owner = newOwner;
    }
