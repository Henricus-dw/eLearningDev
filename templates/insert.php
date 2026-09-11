<!DOCTYPE html>
<html>
    <head>
        <title>Submission Page</title>
    </head>
    <body>
        <h2><a href="manage">View Moderated Forms</a></h2>
        <?php

            echo "STARTING...";
            $servername = "localhost";      // Servername
            $username = "root";             // Database username
            $password = "Proftr@in3179";    // Database password
            $dbname = "moderator";          // Database name

            $conn = new mysqli($servername, $username, $password, $dbname); //Open database connection

            // Check connection
            if ($conn->connect_error) {
                die("Connection failed: " . $conn->connect_error);
            }

            echo "HELLO WORLD??<br>";
		echo "Server arguments: <br>";
		echo $_SERVER['argv'];
		echo "Array: <br>";
		echo $_SERVER['Array'];
		
            foreach($_POST as $variables) {
                echo "POST object:";
                echo $variables. "<br>";
            }

            echo "INSERTING....";

            // Insert submitted form data into the database
            if ($_SERVER["REQUEST_METHOD"] == "POST") {
                // Collect submitted form data
                $studentattemptid = $_POST['studentattemptid'];
                $studentname = $_POST['studentname'];
                $studentid = $_POST['studentid'];
                $coursename = $_POST['coursename'];
                $courseid = $_POST['courseid'];
                $moderatorname = $_POST['moderatorname'];
                $coursecompletiondate = $_POST['coursecompletiondate']; 
                $moderationdate = $_POST['moderationdate'];
                $question1 = $_POST['question1'];
                $question2 = $_POST['question2'];
                $question3 = $_POST['question3'];
                $question4 = $_POST['question4'];
                $question5 = $_POST['question5'];
                $question6 = $_POST['question6'];
                $question7 = $_POST['question7'];
                $feedback = $_POST['feedback'];

                //Check if the student's attempt was already moderated
                $checkDuplicatesql = "SELECT studentattemptid FROM moderationforms WHERE studentattemptid = $studentattemptid";
                $result = $conn->query($checkDuplicatesql);
                
                if ($result->num_rows > 0) {
                    echo "Duplication Error: Student attempt ID: ". $studentattemptid ." has already been moderated.";
                }
                else {
                    // Insert data into the 'moderationforms' table
                    $insertSql = "INSERT INTO moderationforms (studentattemptid, studentname, studentid, coursename, courseid, moderatorname, coursecompletiondate, moderationdate, question1, question2, question3, question4, question5, question6, question7, feedback)
                    VALUES ('$studentattemptid', '$studentname', '$studentid', '$coursename', '$courseid', '$moderatorname', '$coursecompletiondate', '$moderationdate', '$question1', '$question2', '$question3', '$question4', '$question5', '$question6', '$question7', '$feedback')";

                    if ($conn->query($insertSql) === TRUE) {
                        echo "Form submitted successfully!";
                    }
                    else {
                        echo "Form was not submitted because it is not valid.<br>";
                        echo "Validation Error: " . $insertSql . "<br>" . $conn->error;
                    }
                }
                
            }

            echo "EXITING....";

            $conn->close(); //Close database connection
        ?>
    </body>
</html>
