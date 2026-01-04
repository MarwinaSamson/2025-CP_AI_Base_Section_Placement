
from django.core.management.base import BaseCommand
from coordinator_app.models import Qualified_for_ste  # Update with your app name
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Insert student records into Qualified_for_ste'

    def handle(self, *args, **kwargs):
        students = [
            ('111223344556', 'Carlos', 'Garcia', '2010-03-11', 'PQR Primary School'),
            ('222334455667', 'Ana', 'Lopez', '2013-08-25', 'DEF School'),
            ('333445566778', 'Luis', 'Reyes', '2011-11-30', 'GHI Academy'),
            ('444556677889', 'Isabella', 'Morales', '2012-01-05', 'JKL School'),
            ('555667788990', 'Miguel', 'Torres', '2013-07-18', 'MNO Primary School'),
            ('666778899001', 'Sofia', 'Cruz', '2010-12-15', 'NOP School'),
            ('777889900112', 'David', 'Mendez', '2012-06-20', 'QRS Academy'),
            ('888990011223', 'Emma', 'Diaz', '2013-04-07', 'TUV Elementary'),
            ('999001122334', 'Oliver', 'Martinez', '2011-10-30', 'WXY School'),
            ('101234567890', 'Ava', 'Hernandez', '2012-02-25', 'ZAB Academy'),
            ('111234567891', 'James', 'Parker', '2013-09-14', 'CDE School'),
            ('121234567892', 'Mia', 'Rojas', '2010-05-17', 'FGH School'),
            ('131234567893', 'Ethan', 'Ramirez', '2011-03-28', 'IJK Academy'),
            ('141234567894', 'Zoe', 'Gonzalez', '2012-07-02', 'LMN School'),
            ('151234567895', 'Liam', 'Alvarez', '2013-08-18', 'OPQ School'),
            ('161234567896', 'Grace', 'Vargas', '2010-04-26', 'RST Primary School'),
            ('171234567897', 'Noah', 'Castillo', '2012-11-13', 'UVW Academy'),
            ('181234567898', 'Lily', 'Ortega', '2013-01-03', 'XYZ School'),
            ('191234567899', 'Elijah', 'Gutierrez', '2011-12-19', 'ABC Academy'),
            ('201234567890', 'Chloe', 'Sanchez', '2012-09-05', 'DEF School'),
            ('211234567891', 'Lucas', 'Torres', '2010-06-30', 'GHI School'),
            ('221234567892', 'Mila', 'Mora', '2013-10-22', 'JKL Academy'),
            ('231234567893', 'Isaiah', 'Hernandez', '2012-01-15', 'MNO School'),
            ('241234567894', 'Layla', 'Solis', '2011-11-16', 'PQR Academy'),
            ('251234567895', 'Gabriel', 'Palacios', '2010-02-11', 'STU School'),
            ('261234567896', 'Nora', 'Ruiz', '2013-05-09', 'VWX Academy'),
            ('271234567897', 'Cameron', 'Valenzuela', '2012-08-28', 'YZA School'),
            ('281234567898', 'Savannah', 'Trejo', '2011-09-17', 'BCD Academy'),
            ('291234567899', 'Eric', 'Bautista', '2013-04-12', 'EFG School'),
            ('301234567890', 'Kylie', 'Olivares', '2011-10-27', 'HIJ Primary School'),
            ('311234567891', 'Parker', 'Escobar', '2010-03-15', 'KLM Academy'),
            ('321234567892', 'Skylar', 'Luna', '2012-06-23', 'NOP School'),
            ('331234567893', 'Wyatt', 'Mendez', '2013-09-20', 'QRS Academy'),
            ('341234567894', 'Riley', 'Cervantes', '2012-05-08', 'TUV School'),
            ('351234567895', 'Levi', 'Salazar', '2011-02-14', 'WXY Academy'),
            ('361234567896', 'Madison', 'Martinez', '2010-04-25', 'ZAB School'),
            ('371234567897', 'Jaxon', 'Reyes', '2013-11-16', 'CDE Academy'),
            ('381234567898', 'Ella', 'Gonzalez', '2012-01-30', 'FGH School'),
            ('391234567899', 'Anthony', 'Pena', '2011-03-29', 'IJK Academy'),
            ('401234567890', 'Caroline', 'Hernandez', '2012-12-05', 'LMN School'),
            ('411234567891', 'Hunter', 'Gonzalez', '2010-11-18', 'OPQ Academy'),
            ('421234567892', 'Victoria', 'Morales', '2013-06-14', 'RST School'),
            ('431234567893', 'Matthew', 'Ramirez', '2012-02-09', 'UVW Academy'),
            ('441234567894', 'Addison', 'Diaz', '2011-07-17', 'XYZ School'),
            ('451234567895', 'Nathan', 'Sanchez', '2010-08-30', 'ABC Academy'),
            ('461234567896', 'Aubrey', 'Salinas', '2013-03-24', 'DEF School'),
            ('471234567897', 'Owen', 'Cortez', '2011-05-29', 'GHI Academy'),
            ('481234567898', 'Hailey', 'Soto', '2012-09-22', 'JKL School'),
            ('491234567899', 'Samuel', 'Rojas', '2013-01-06', 'MNO Primary School'),
            ('501234567890', 'Scarlett', 'Guerrero', '2010-10-10', 'PQR Academy'),
            ('511234567891', 'Dylan', 'Hernandez', '2012-04-01', 'TUV School'),
            ('521234567892', 'Alyssa', 'Mendez', '2013-05-11', 'WXY Academy'),
        ]

        for student in students:
            student_lrn, first_name, last_name, dob, school_name = student
            qualified_record = Qualified_for_ste(
                student_lrn=student_lrn,
                exam_score=85.0,  # Example score
                interview_score=90.0,  # Example score
                status='qualified',  # Example status
                updated_by=User.objects.get(id=5),  # Assuming a user with ID 5
                remarks=f'Student from {school_name}.'
            )
            qualified_record.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully inserted: {qualified_record}'))

        self.stdout.write(self.style.SUCCESS("All records inserted successfully!"))