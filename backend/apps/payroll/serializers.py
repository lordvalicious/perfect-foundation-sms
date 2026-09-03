from rest_framework import serializers

from .models import PayrollRecord, Payslip, SalaryStructure


class SalaryStructureSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )
    total_allowances = serializers.DecimalField(
        read_only=True,
        max_digits=12,
        decimal_places=2,
    )
    gross_salary = serializers.DecimalField(
        read_only=True,
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        model = SalaryStructure
        fields = [
            "id",
            "employee",
            "teacher_name",
            "basic_salary",
            "total_allowances",
            "gross_salary",
            "effective_date",
            "status",
        ]


class PayrollRecordSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="employee.full_name",
        read_only=True,
    )
    teacher_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )
    structure_basic = serializers.DecimalField(
        source="salary_structure.basic_salary",
        read_only=True,
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        model = PayrollRecord
        fields = [
            "id",
            "employee",
            "teacher_name",
            "teacher_number",
            "salary_structure",
            "structure_basic",
            "month",
            "year",
            "working_days",
            "paid_days",
            "basic_salary",
            "total_allowances",
            "gross_salary",
            "total_deductions",
            "net_salary",
            "status",
            "processed_at",
            "created_at",
        ]
        read_only_fields = [
            "basic_salary",
            "allowances",
            "gross_salary",
            "total_deductions",
            "net_salary",
            "processed_at",
        ]

    def create(self, validated_data):
        record = PayrollRecord.objects.create(**validated_data)
        return record


class PayslipSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="record.employee.full_name",
        read_only=True,
    )
    period = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = [
            "id",
            "record",
            "teacher_name",
            "period",
            "document",
            "issued_at",
        ]

    def get_period(self, obj):
        return f"{obj.record.month:02d}-{obj.record.year}"
