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