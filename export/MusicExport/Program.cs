using System;
using System.Data;
using System.IO;
using ClosedXML.Excel;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace MusicExport
{
    class Program
    {
        static void Main(string[] args)
        {
            if(args.Length < 2)
            {
                Console.WriteLine("Usage: MusicExport <input_json_file> <output_excel_file>");
                return;
            }
            
            string jsonFile = args[0];
            string outputExcel = args[1];

            try
            {
                var jsonData = File.ReadAllText(jsonFile);
                var dataArray = JsonConvert.DeserializeObject<JArray>(jsonData);
                
                DataTable dt = new DataTable();
                if (dataArray.Count > 0)
                {
                    foreach (JProperty prop in ((JObject)dataArray[0]).Properties())
                    {
                        dt.Columns.Add(prop.Name);
                    }

                    foreach (JObject obj in dataArray)
                    {
                        DataRow row = dt.NewRow();
                        foreach (DataColumn col in dt.Columns)
                        {
                            row[col.ColumnName] = obj[col.ColumnName]?.ToString();
                        }
                        dt.Rows.Add(row);
                    }
                }

                using (var workbook = new XLWorkbook())
                {
                    var worksheet = workbook.Worksheets.Add("Music Report");
                    worksheet.Cell(1, 1).InsertTable(dt);
                    workbook.SaveAs(outputExcel);
                }
                Console.WriteLine("Excel file generated: " + outputExcel);
            }
            catch (Exception ex)
            {
                Console.WriteLine("Error in C# export application: " + ex.Message);
            }
        }
    }
}